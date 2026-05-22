"""
LightGCN — Graph-based collaborative filter.

Propagates embeddings through the user-item bipartite graph:

    e_u^(l+1) = Σ_{i∈N(u)}  1/√(|N(u)|·|N(i)|) · e_i^(l)
    e_i^(l+1) = Σ_{u∈N(i)}  1/√(|N(u)|·|N(i)|) · e_u^(l)

Final embedding = mean over all L+1 layers.
Trained with BPR (Bayesian Personalised Ranking) pairwise loss.

Reference: He et al., "LightGCN: Simplifying and Powering Graph Convolution
Network for Recommendation", SIGIR 2020.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .base import BaseRecommender


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -30, 30)))


class LightGCN(BaseRecommender):
    """
    LightGCN collaborative filter.

    Parameters
    ----------
    n_factors : int
        Embedding dimensionality.
    n_epochs : int
        Training epochs (upper bound; early stopping may cut earlier).
    lr : float
        Learning rate.
    reg : float
        L2 regularisation on embeddings.
    n_layers : int
        Number of graph propagation layers (L in the paper).
    batch_size : int
        Mini-batch size for BPR training.
    patience : int
        Early-stopping patience (epochs without improvement on BPR loss).
    min_delta : float
        Minimum improvement required to reset patience counter.
    seed : int
        RNG seed for reproducibility (embedding init + negative sampling).
    """

    def __init__(
        self,
        n_factors: int = 64,
        n_epochs: int = 100,
        lr: float = 0.005,
        reg: float = 1e-4,
        n_layers: int = 3,
        batch_size: int = 4096,
        patience: int = 10,
        min_delta: float = 1e-4,
        seed: int = 42,
    ) -> None:
        self.n_factors = n_factors
        self.n_epochs = n_epochs
        self.lr = lr
        self.reg = reg
        self.n_layers = n_layers
        self.batch_size = batch_size
        self.patience = patience
        self.min_delta = min_delta
        self.seed = seed
        self.loss_history: list[float] = []

    # ── Graph propagation ─────────────────────────────────────────────────

    def _propagate(
        self, Eu: np.ndarray, Ei: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Perform L rounds of light graph convolution.
        Returns final (user_emb, item_emb) as the mean across all layers.
        """
        all_eu = [Eu]
        all_ei = [Ei]
        for _ in range(self.n_layers):
            new_eu = np.zeros_like(Eu)
            new_ei = np.zeros_like(Ei)
            np.add.at(new_eu, self._u_ids, self._norms[:, None] * Ei[self._i_ids])
            np.add.at(new_ei, self._i_ids, self._norms[:, None] * Eu[self._u_ids])
            Eu, Ei = new_eu, new_ei
            all_eu.append(Eu)
            all_ei.append(Ei)
        return np.mean(all_eu, axis=0), np.mean(all_ei, axis=0)

    # ── Bias fitting (only used once after training for final inference) ──

    def _fit_biases(
        self,
        Eu: np.ndarray,
        Ei: np.ndarray,
        u_ids: np.ndarray,
        i_ids: np.ndarray,
        ratings: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Fit mu + bu + bi by least-squares on residuals."""
        scores = (Eu[u_ids] * Ei[i_ids]).sum(1)
        res = ratings - scores - self.mu
        bu = np.zeros(self._n_users, np.float32)
        np.add.at(bu, u_ids, res)
        bu /= np.bincount(u_ids, minlength=self._n_users).clip(1)
        res2 = ratings - scores - self.mu - bu[u_ids]
        bi = np.zeros(self._n_items, np.float32)
        np.add.at(bi, i_ids, res2)
        bi /= np.bincount(i_ids, minlength=self._n_items).clip(1)
        return bu, bi

    # ── Negative sampling (filters seen items per user) ──────────────────

    def _sample_negatives(self, rng, u_batch: np.ndarray) -> np.ndarray:
        """
        Sample one negative per row in u_batch, guaranteed to not be in
        ``self._seen[u]``.  Uses rejection sampling with a few retries;
        in the rare case all retries collide with seen items, accepts the
        last draw (never hangs).
        """
        n_items = self._n_items
        negs = rng.integers(0, n_items, size=len(u_batch)).astype(np.int32)
        max_retries = 5
        for _ in range(max_retries):
            collision_mask = np.array(
                [int(neg) in self._seen.get(int(u), ()) for u, neg in zip(u_batch, negs)]
            )
            if not collision_mask.any():
                break
            negs[collision_mask] = rng.integers(0, n_items, size=collision_mask.sum()).astype(np.int32)
        return negs

    # ── Training ──────────────────────────────────────────────────────────

    def fit(self, ratings: pd.DataFrame) -> "LightGCN":
        """Fit model on the given ratings DataFrame."""
        rng = np.random.default_rng(self.seed)

        self._u_ids = ratings["user_id"].values.astype(np.int32)
        self._i_ids = ratings["movie_idx"].values.astype(np.int32)
        r = ratings["rating"].values.astype(np.float32)

        n_users = int(self._u_ids.max()) + 1
        n_items = int(self._i_ids.max()) + 1
        self._n_users = n_users
        self._n_items = n_items
        self.mu = float(r.mean())

        # Seen items per user — used by neg sampling and inference filtering
        self._seen: dict[int, set[int]] = (
            ratings.groupby("user_id")["movie_idx"].apply(set).to_dict()
        )

        # Degree-normalised edge weights: 1 / √(deg_u · deg_i)
        u_deg = np.bincount(self._u_ids, minlength=n_users).astype(np.float32)
        i_deg = np.bincount(self._i_ids, minlength=n_items).astype(np.float32)
        self._norms = (
            1.0 / np.sqrt(u_deg[self._u_ids].clip(1) * i_deg[self._i_ids].clip(1))
        ).astype(np.float32)

        # Base (learnable) embeddings — seeded for reproducibility
        self.Eu0 = rng.normal(0, 0.1, (n_users, self.n_factors)).astype(np.float32)
        self.Ei0 = rng.normal(0, 0.1, (n_items, self.n_factors)).astype(np.float32)

        # Early stopping state (tracks BPR loss — ranking objective)
        best_loss = float("inf")
        best_Eu0 = self.Eu0.copy()
        best_Ei0 = self.Ei0.copy()
        epochs_without_improvement = 0

        for _ in range(self.n_epochs):
            Eu, Ei = self._propagate(self.Eu0, self.Ei0)

            idx = rng.permutation(len(self._u_ids))
            epoch_loss = 0.0
            n_batches = 0
            for s in range(0, len(idx), self.batch_size):
                b = idx[s : s + self.batch_size]
                u = self._u_ids[b]
                pos = self._i_ids[b]
                neg = self._sample_negatives(rng, u)

                eu = Eu[u]
                ei_p = Ei[pos]
                ei_n = Ei[neg]

                diff = (eu * (ei_p - ei_n)).sum(1)
                sig = _sigmoid(-diff)

                # BPR loss for this batch (negative log-sigmoid of diff)
                epoch_loss += float(-np.log(_sigmoid(diff)).mean())
                n_batches += 1

                np.add.at(self.Eu0, u, self.lr * (sig[:, None] * (ei_p - ei_n) - self.reg * self.Eu0[u]))
                np.add.at(self.Ei0, pos, self.lr * (sig[:, None] * eu - self.reg * self.Ei0[pos]))
                np.add.at(self.Ei0, neg, self.lr * (-sig[:, None] * eu - self.reg * self.Ei0[neg]))

            avg_loss = epoch_loss / max(n_batches, 1)
            self.loss_history.append(avg_loss)

            # Early stopping based on BPR loss (matches ranking objective)
            if avg_loss < best_loss - self.min_delta:
                best_loss = avg_loss
                best_Eu0 = self.Eu0.copy()
                best_Ei0 = self.Ei0.copy()
                epochs_without_improvement = 0
            else:
                epochs_without_improvement += 1
                if epochs_without_improvement >= self.patience:
                    break

        # Restore best embeddings
        self.Eu0 = best_Eu0
        self.Ei0 = best_Ei0

        # Materialise final embeddings for fast inference
        self._Eu_final, self._Ei_final = self._propagate(self.Eu0, self.Ei0)
        self.bu, self.bi = self._fit_biases(
            self._Eu_final, self._Ei_final, self._u_ids, self._i_ids, r
        )

        # Precompute score matrix once: O(n_users × n_items × n_factors)
        # For 10k users × 5k items × 64 factors this is ~200MB but eliminates
        # the per-inference cost entirely.
        self._all_scores = (
            self.mu
            + self.bu[:, None]
            + self.bi[None, :]
            + self._Eu_final @ self._Ei_final.T
        ).astype(np.float32)

        return self

    # ── Inference ─────────────────────────────────────────────────────────

    def recommend(
        self,
        user_id: int,
        n: int = 10,
        exclude: set[int] | None = None,
    ) -> list[int]:
        scores = self._raw_scores(user_id)
        if scores is None:
            return []
        scores = scores.copy()
        seen = self._seen.get(user_id, set())
        if exclude:
            seen = seen | exclude
        for idx in seen:
            if 0 <= idx < len(scores):
                scores[idx] = -np.inf
        return np.argsort(scores)[::-1][:n].tolist()

    def _raw_scores(self, user_id: int) -> np.ndarray | None:
        if user_id < 0 or user_id >= self._n_users:
            return None
        return self._all_scores[user_id]

    def score_all(self, user_id: int) -> np.ndarray | None:
        return self._raw_scores(user_id)

    # ── Persistence ───────────────────────────────────────────────────────

    def save(self, path: str | Path) -> None:
        """Save model weights to a .npz file. Also persists `_seen` as sidecar JSON."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez(
            path,
            Eu0=self.Eu0,
            Ei0=self.Ei0,
            Eu_final=self._Eu_final,
            Ei_final=self._Ei_final,
            u_ids=self._u_ids,
            i_ids=self._i_ids,
            norms=self._norms,
            mu=np.array([self.mu]),
            bu=self.bu,
            bi=self.bi,
            all_scores=self._all_scores,
        )
        # Save `_seen` alongside the .npz so recommend() excludes seen items
        seen_path = path.with_suffix(".seen.json")
        with open(seen_path, "w") as f:
            json.dump({str(k): sorted(int(x) for x in v) for k, v in self._seen.items()}, f)

    @classmethod
    def load(cls, path: str | Path, **kwargs) -> "LightGCN":
        """Load a saved model (fast path — skips training)."""
        path = Path(path)
        data = np.load(path)
        obj = cls(**kwargs)
        obj.Eu0 = data["Eu0"]
        obj.Ei0 = data["Ei0"]
        obj._Eu_final = data["Eu_final"]
        obj._Ei_final = data["Ei_final"]
        obj._u_ids = data["u_ids"]
        obj._i_ids = data["i_ids"]
        obj._norms = data["norms"]
        obj.mu = float(data["mu"][0])
        obj.bu = data["bu"]
        obj.bi = data["bi"]
        obj._n_users = int(obj.Eu0.shape[0])
        obj._n_items = int(obj.Ei0.shape[0])
        obj._all_scores = (
            data["all_scores"]
            if "all_scores" in data.files
            else (obj.mu + obj.bu[:, None] + obj.bi[None, :] + obj._Eu_final @ obj._Ei_final.T).astype(np.float32)
        )
        # Restore `_seen` from sidecar JSON if it exists
        seen_path = path.with_suffix(".seen.json")
        if seen_path.exists():
            with open(seen_path) as f:
                raw = json.load(f)
            obj._seen = {int(k): set(v) for k, v in raw.items()}
        else:
            obj._seen = {}
        return obj
