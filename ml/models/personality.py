"""
Personality-based recommender (cold-start).

PersonalityMLPRecommender: maps Big Five personality traits to the collaborative
filtering user-embedding space via a 3-layer MLP, trained with BPR loss against
pre-computed item embeddings from LightGCN.

At inference only the personality vector is required (cold-start).
Implementation is pure NumPy (no PyTorch dependency) for consistency with
the rest of the ml/ package.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .base import BaseRecommender

TRAIT_COLS = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -30, 30)))


def _relu(x: np.ndarray) -> np.ndarray:
    return np.maximum(0.0, x)


class _MLP:
    """3-layer MLP (5 → H → H → D) with ReLU and forward-pass dropout."""

    def __init__(self, in_dim: int, hidden: int, out_dim: int, seed: int) -> None:
        rng = np.random.default_rng(seed)
        # He init
        self.W1 = rng.standard_normal((in_dim, hidden)).astype(np.float32) * np.sqrt(2.0 / in_dim)
        self.b1 = np.zeros(hidden, dtype=np.float32)
        self.W2 = rng.standard_normal((hidden, hidden)).astype(np.float32) * np.sqrt(2.0 / hidden)
        self.b2 = np.zeros(hidden, dtype=np.float32)
        self.W3 = rng.standard_normal((hidden, out_dim)).astype(np.float32) * np.sqrt(2.0 / hidden)
        self.b3 = np.zeros(out_dim, dtype=np.float32)

    def params(self) -> list[np.ndarray]:
        return [self.W1, self.b1, self.W2, self.b2, self.W3, self.b3]

    def forward(self, x: np.ndarray, dropout: float = 0.0, rng: np.random.Generator | None = None):
        """Returns (output, cache) for backward pass."""
        z1 = x @ self.W1 + self.b1
        a1 = _relu(z1)
        if dropout > 0.0 and rng is not None:
            m1 = (rng.random(a1.shape) > dropout).astype(np.float32) / (1.0 - dropout)
            a1 = a1 * m1
        else:
            m1 = None
        z2 = a1 @ self.W2 + self.b2
        a2 = _relu(z2)
        if dropout > 0.0 and rng is not None:
            m2 = (rng.random(a2.shape) > dropout).astype(np.float32) / (1.0 - dropout)
            a2 = a2 * m2
        else:
            m2 = None
        out = a2 @ self.W3 + self.b3
        cache = (x, z1, a1, m1, z2, a2, m2)
        return out, cache

    def backward(self, d_out: np.ndarray, cache) -> list[np.ndarray]:
        """Compute parameter gradients given d(loss)/d(output)."""
        x, z1, a1, m1, z2, a2, m2 = cache
        dW3 = a2.T @ d_out
        db3 = d_out.sum(axis=0)
        da2 = d_out @ self.W3.T
        if m2 is not None:
            da2 = da2 * m2
        dz2 = da2 * (z2 > 0).astype(np.float32)
        dW2 = a1.T @ dz2
        db2 = dz2.sum(axis=0)
        da1 = dz2 @ self.W2.T
        if m1 is not None:
            da1 = da1 * m1
        dz1 = da1 * (z1 > 0).astype(np.float32)
        dW1 = x.T @ dz1
        db1 = dz1.sum(axis=0)
        return [dW1, db1, dW2, db2, dW3, db3]


class _Adam:
    """Adam optimizer over a list of parameter arrays (in-place updates)."""

    def __init__(self, params: list[np.ndarray], lr: float, weight_decay: float = 0.0) -> None:
        self.params = params
        self.lr = lr
        self.wd = weight_decay
        self.m = [np.zeros_like(p) for p in params]
        self.v = [np.zeros_like(p) for p in params]
        self.t = 0
        self.beta1 = 0.9
        self.beta2 = 0.999
        self.eps = 1e-8

    def step(self, grads: list[np.ndarray]) -> None:
        self.t += 1
        for i, (p, g) in enumerate(zip(self.params, grads)):
            if self.wd > 0.0:
                g = g + self.wd * p
            self.m[i] = self.beta1 * self.m[i] + (1.0 - self.beta1) * g
            self.v[i] = self.beta2 * self.v[i] + (1.0 - self.beta2) * (g * g)
            m_hat = self.m[i] / (1.0 - self.beta1 ** self.t)
            v_hat = self.v[i] / (1.0 - self.beta2 ** self.t)
            p -= self.lr * m_hat / (np.sqrt(v_hat) + self.eps)


class PersonalityMLPRecommender(BaseRecommender):
    """
    Personality → user-embedding MLP, scored against pre-trained item embeddings.

    Architecture:
      - MLP: 5 traits → hidden → hidden → embedding_dim
      - Item embeddings (frozen) from a CF model like LightGCN
      - Learned per-item bias
      - Score(u, i) = user_emb(traits_u) @ item_emb[i] + b_item[i]

    Loss: BPR with uniform negative sampling (excluding seen items).
    Cold-start: at inference only the 5 traits are needed.
    """

    def __init__(
        self,
        personalities: pd.DataFrame,
        cf_item_embeddings: np.ndarray,
        embedding_dim: int = 64,
        hidden_dim: int = 128,
        dropout: float = 0.3,
        lr: float = 1e-3,
        weight_decay: float = 1e-4,
        n_epochs: int = 50,
        batch_size: int = 1024,
        patience: int = 5,
        val_frac: float = 0.1,
        popularity_penalty: float = 0.0,
        normalize_items: bool = False,
        mmr_lambda: float | None = None,
        cosine_sim: np.ndarray | None = None,
        mmr_pool: int = 50,
        seed: int = 42,
    ) -> None:
        self._embedding_dim = int(embedding_dim)
        self._hidden_dim = int(hidden_dim)
        self._dropout = float(dropout)
        self._lr = float(lr)
        self._weight_decay = float(weight_decay)
        self._n_epochs = int(n_epochs)
        self._batch_size = int(batch_size)
        self._patience = int(patience)
        self._val_frac = float(val_frac)
        self._popularity_penalty = float(popularity_penalty)
        self._normalize_items = bool(normalize_items)
        self._mmr_lambda = mmr_lambda
        self._cosine_sim = cosine_sim
        self._mmr_pool = int(mmr_pool)
        self._seed = int(seed)

        # Personality lookup
        traits_arr = personalities[TRAIT_COLS].to_numpy(dtype=np.float32)
        self._trait_mean = traits_arr.mean(axis=0)
        self._trait_std = traits_arr.std(axis=0).clip(1e-6)
        normed = (traits_arr - self._trait_mean) / self._trait_std
        self._traits: dict[int, np.ndarray] = {
            int(uid): normed[i] for i, uid in enumerate(personalities["user_id"].values)
        }

        # Frozen item embeddings (optionally L2-normalized to remove popularity bias)
        Ei = cf_item_embeddings.astype(np.float32)
        if self._normalize_items:
            norms = np.linalg.norm(Ei, axis=1, keepdims=True)
            norms = np.where(norms < 1e-8, 1.0, norms)
            Ei = Ei / norms
        self._Ei = Ei
        self._n_items = self._Ei.shape[0]

        self._mlp: _MLP | None = None
        self._item_bias: np.ndarray | None = None
        self._item_popularity: np.ndarray | None = None
        self._user_seen: dict[int, set[int]] = {}

    def set_personalities(self, personalities: pd.DataFrame) -> None:
        """
        Swap the personality lookup without re-training.

        Used for cross-dataset evaluation: a model trained on one dataset
        can be applied to users of another dataset by injecting their
        personality traits. The model's learned MLP and item bias are
        preserved; only the input lookup is replaced.

        Uses the ORIGINAL trait_mean/trait_std (computed at __init__) so
        the MLP receives inputs on the same scale it was trained on.
        """
        traits_arr = personalities[TRAIT_COLS].to_numpy(dtype=np.float32)
        normed = (traits_arr - self._trait_mean) / self._trait_std
        self._traits = {
            int(uid): normed[i] for i, uid in enumerate(personalities["user_id"].values)
        }
        # Reset seen map (caller must re-fit or provide new seen if needed)
        self._user_seen = {}

    def _user_emb(self, traits: np.ndarray, training: bool = False,
                  rng: np.random.Generator | None = None):
        dropout = self._dropout if training else 0.0
        out, cache = self._mlp.forward(traits, dropout=dropout, rng=rng)
        return out, cache

    def fit(self, ratings: pd.DataFrame) -> None:
        rng = np.random.default_rng(self._seed)

        # Build seen map (for suppression + training neg sampling)
        self._user_seen = {}
        for uid, mid in zip(ratings["user_id"].values, ratings["movie_idx"].values):
            self._user_seen.setdefault(int(uid), set()).add(int(mid))

        # Positives: rating >= 4 AND user has personality AND item within embeddings
        pos = ratings[ratings["rating"] >= 4.0][["user_id", "movie_idx"]].copy()
        pos = pos[pos["user_id"].isin(self._traits.keys())]
        pos = pos[pos["movie_idx"] < self._n_items].reset_index(drop=True)

        # Initialise MLP and item bias
        self._mlp = _MLP(5, self._hidden_dim, self._embedding_dim, self._seed)
        self._item_bias = np.zeros(self._n_items, dtype=np.float32)

        # Compute item popularity (log-scaled, min-max normalized to [0, 1])
        item_counts = np.bincount(
            ratings["movie_idx"].values.astype(np.int32), minlength=self._n_items
        ).astype(np.float32)
        log_pop = np.log1p(item_counts)
        lo, hi = log_pop.min(), log_pop.max()
        self._item_popularity = (log_pop - lo) / (hi - lo) if hi > lo else np.zeros_like(log_pop)

        if len(pos) < 10:
            return  # not enough data; keep random init for cold-start demos

        # Train/val split
        n = len(pos)
        perm = rng.permutation(n)
        n_val = max(1, int(n * self._val_frac))
        val_idx, train_idx = perm[:n_val], perm[n_val:]
        train_pos = pos.iloc[train_idx].reset_index(drop=True)
        val_pos = pos.iloc[val_idx].reset_index(drop=True)

        train_uids = train_pos["user_id"].to_numpy(dtype=np.int64)
        train_pos_items = train_pos["movie_idx"].to_numpy(dtype=np.int64)
        val_uids = val_pos["user_id"].to_numpy(dtype=np.int64)
        val_pos_items = val_pos["movie_idx"].to_numpy(dtype=np.int64)

        train_traits = np.stack([self._traits[int(u)] for u in train_uids])
        val_traits = np.stack([self._traits[int(u)] for u in val_uids])

        seen_arr = [self._user_seen.get(int(u), set()) for u in train_uids]

        opt = _Adam(self._mlp.params() + [self._item_bias],
                    lr=self._lr, weight_decay=self._weight_decay)

        n_train = len(train_pos)
        best_val_loss = float("inf")
        patience_ct = 0
        best_params = None

        for epoch in range(self._n_epochs):
            perm_epoch = rng.permutation(n_train)

            for b_start in range(0, n_train, self._batch_size):
                b_idx = perm_epoch[b_start : b_start + self._batch_size]
                bs = len(b_idx)

                # Sample negatives uniformly, re-sample once if in seen
                neg_items = rng.integers(0, self._n_items, size=bs)
                for i, bi in enumerate(b_idx):
                    if int(neg_items[i]) in seen_arr[bi]:
                        neg_items[i] = rng.integers(0, self._n_items)

                t_batch = train_traits[b_idx]
                pos_b = train_pos_items[b_idx]

                # Forward
                u, cache = self._user_emb(t_batch, training=True, rng=rng)     # (B, D)
                pos_emb = self._Ei[pos_b]                                       # (B, D)
                neg_emb = self._Ei[neg_items]                                   # (B, D)
                pos_score = (u * pos_emb).sum(axis=1) + self._item_bias[pos_b]  # (B,)
                neg_score = (u * neg_emb).sum(axis=1) + self._item_bias[neg_items]
                diff = pos_score - neg_score
                sig = _sigmoid(-diff)                                           # (B,)
                # Loss = -log(sigmoid(diff)); dL/d(diff) = -sigmoid(-diff) = -sig
                # Backward
                d_diff = -sig / bs                                              # (B,)
                d_u = d_diff[:, None] * (pos_emb - neg_emb)                     # (B, D)
                d_bi_pos = d_diff                                               # (B,)
                d_bi_neg = -d_diff                                              # (B,)

                grads = self._mlp.backward(d_u, cache)

                # Item bias gradient (sparse accumulation)
                d_bias = np.zeros_like(self._item_bias)
                np.add.at(d_bias, pos_b, d_bi_pos)
                np.add.at(d_bias, neg_items, d_bi_neg)

                opt.step(grads + [d_bias])

            # Validation BPR loss
            neg_val = rng.integers(0, self._n_items, size=len(val_pos))
            uv, _ = self._user_emb(val_traits, training=False)
            pos_s = (uv * self._Ei[val_pos_items]).sum(axis=1) + self._item_bias[val_pos_items]
            neg_s = (uv * self._Ei[neg_val]).sum(axis=1) + self._item_bias[neg_val]
            val_loss = float(-np.log(_sigmoid(pos_s - neg_s) + 1e-12).mean())

            if val_loss < best_val_loss - 1e-4:
                best_val_loss = val_loss
                patience_ct = 0
                best_params = [p.copy() for p in self._mlp.params()] + [self._item_bias.copy()]
            else:
                patience_ct += 1
                if patience_ct >= self._patience:
                    break

        # Restore best
        if best_params is not None:
            mlp_params = self._mlp.params()
            for i, p in enumerate(best_params[:-1]):
                mlp_params[i][:] = p
            self._item_bias[:] = best_params[-1]

    def score_all(self, user_id: int) -> np.ndarray | None:
        if self._mlp is None:
            return None
        traits = self._traits.get(int(user_id))
        if traits is None:
            return None
        u, _ = self._user_emb(traits[None, :], training=False)   # (1, D)
        scores = (u @ self._Ei.T).ravel() + self._item_bias      # (n_items,)
        if self._popularity_penalty > 0.0 and self._item_popularity is not None:
            std = scores.std()
            if std > 1e-8:
                scores = scores - self._popularity_penalty * std * self._item_popularity
        return scores

    def _mmr_rerank(self, pool: list[int], scores: np.ndarray, n: int) -> list[int]:
        lam = self._mmr_lambda
        selected: list[int] = []
        remaining = list(pool)
        while remaining and len(selected) < n:
            if not selected:
                best = max(remaining, key=lambda i: scores[i])
            else:
                best = max(
                    remaining,
                    key=lambda i: (
                        lam * scores[i]
                        - (1 - lam) * float(np.max(self._cosine_sim[i, selected]))
                    ),
                )
            selected.append(best)
            remaining.remove(best)
        return selected

    def recommend(
        self, user_id: int, n: int = 10, exclude: set[int] | None = None
    ) -> list[int]:
        scores = self.score_all(user_id)
        if scores is None:
            return []
        to_suppress = set(self._user_seen.get(int(user_id), set()))
        if exclude:
            to_suppress |= exclude
        scores = scores.copy()
        for idx in to_suppress:
            if 0 <= idx < len(scores):
                scores[idx] = -np.inf

        if self._mmr_lambda is not None and self._cosine_sim is not None:
            pool = np.argsort(-scores)[:max(n, self._mmr_pool)].tolist()
            return self._mmr_rerank(pool, scores, n)
        return np.argsort(-scores)[:n].tolist()
