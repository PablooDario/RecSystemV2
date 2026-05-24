"""
Personality-based recommender (cold-start).

PersonalityMLPRecommender: maps Big Five personality traits to the collaborative
filtering user-embedding space via either a Linear or MLP head, trained with
BPR loss against pre-computed item embeddings from LightGCN.

At inference only the personality vector is required (cold-start).
Implementation is pure NumPy (no PyTorch dependency) for consistency with
the rest of the ml/ package.

Configurable structural choices (Fase B):
- model_type: 'linear' (5→D direct) or 'mlp' (5→H→H→D with ReLU+dropout)
- whiten_items: apply ZCA whitening to frozen item embeddings to decorrelate
  the latent dimensions and reduce the popular-direction bias.
- feature_mode: 'raw', 'quantile' (uniform percentiles), or 'quantile_cross'
  (percentiles + 5 trait interaction terms).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .base import BaseRecommender
from .coherent_rerank import (
    build_extended_nave,
    build_item_genres,
    compute_user_genre_affinity,
    coherent_rerank,
)

TRAIT_COLS = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]

# 5 hand-picked trait interaction terms (psychologically meaningful pairs).
_CROSS_PAIRS = [
    ("openness", "conscientiousness"),
    ("openness", "neuroticism"),
    ("extraversion", "agreeableness"),
    ("conscientiousness", "neuroticism"),
    ("openness", "extraversion"),
]


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -30, 30)))


def _relu(x: np.ndarray) -> np.ndarray:
    return np.maximum(0.0, x)


def _zca_whitening_matrix(X: np.ndarray, eps: float = 1e-5) -> np.ndarray:
    """Compute ZCA whitening matrix for the rows of X (items × dim)."""
    Xc = X - X.mean(axis=0, keepdims=True)
    cov = Xc.T @ Xc / max(1, Xc.shape[0] - 1)
    U, S, _ = np.linalg.svd(cov)
    W = U @ np.diag(1.0 / np.sqrt(S + eps)) @ U.T
    return W.astype(np.float32)


class _Linear:
    """Single linear layer (in_dim → out_dim) — no activation, no dropout."""

    def __init__(self, in_dim: int, out_dim: int, seed: int) -> None:
        rng = np.random.default_rng(seed)
        # Xavier init suited for linear (no ReLU)
        self.W1 = rng.standard_normal((in_dim, out_dim)).astype(np.float32) * np.sqrt(1.0 / in_dim)
        self.b1 = np.zeros(out_dim, dtype=np.float32)

    def params(self) -> list[np.ndarray]:
        return [self.W1, self.b1]

    def forward(self, x: np.ndarray, dropout: float = 0.0, rng=None):
        out = x @ self.W1 + self.b1
        cache = (x,)
        return out, cache

    def backward(self, d_out: np.ndarray, cache) -> list[np.ndarray]:
        (x,) = cache
        dW1 = x.T @ d_out
        db1 = d_out.sum(axis=0)
        return [dW1, db1]


class _MLP:
    """3-layer MLP (in_dim → H → H → out_dim) with ReLU and forward-pass dropout."""

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


def _quantile_transform(traits_arr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Map each column to its empirical CDF (uniform [0, 1]).
    Returns (transformed, sorted_columns) for inference.
    """
    sorted_cols = np.sort(traits_arr, axis=0)
    n = sorted_cols.shape[0]
    transformed = np.empty_like(traits_arr, dtype=np.float32)
    for j in range(traits_arr.shape[1]):
        ranks = np.searchsorted(sorted_cols[:, j], traits_arr[:, j], side="right")
        transformed[:, j] = ranks / n
    return transformed.astype(np.float32), sorted_cols.astype(np.float32)


def _apply_quantile(traits_arr: np.ndarray, sorted_cols: np.ndarray) -> np.ndarray:
    """Apply previously-fit quantile transform to new traits."""
    n = sorted_cols.shape[0]
    out = np.empty_like(traits_arr, dtype=np.float32)
    for j in range(traits_arr.shape[1]):
        ranks = np.searchsorted(sorted_cols[:, j], traits_arr[:, j], side="right")
        out[:, j] = ranks / n
    return out


def _add_cross_features(traits_df: pd.DataFrame, base_arr: np.ndarray) -> np.ndarray:
    """Append 5 hand-picked trait interaction terms to the base features."""
    extras = []
    for a, b in _CROSS_PAIRS:
        ai = TRAIT_COLS.index(a)
        bi = TRAIT_COLS.index(b)
        extras.append(base_arr[:, ai] * base_arr[:, bi])
    cross = np.stack(extras, axis=1).astype(np.float32)
    return np.concatenate([base_arr, cross], axis=1)


class PersonalityMLPRecommender(BaseRecommender):
    """
    Personality → user-embedding model, scored against pre-trained item embeddings.

    Architecture:
      - Head: Linear (5→D) or 3-layer MLP (5→H→H→D)
      - Item embeddings (frozen) from LightGCN, optionally ZCA-whitened
      - Learned per-item bias
      - Score(u, i) = head(traits_u) @ item_emb[i] + b_item[i]

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
        pop_gamma: float = 1.0,
        normalize_items: bool = False,
        whiten_items: bool = False,
        model_type: str = "mlp",
        feature_mode: str = "raw",
        mmr_lambda: float | None = None,
        cosine_sim: np.ndarray | None = None,
        mmr_pool: int = 50,
        coherent: bool = False,
        movies_df: pd.DataFrame | None = None,
        primary_slots: int = 7,
        wildcard_slots: int = 2,
        free_slots: int = 1,
        primary_top_k: int = 1,
        wildcard_top_k: int = 3,
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
        self._pop_gamma = float(pop_gamma)
        self._normalize_items = bool(normalize_items)
        self._whiten_items = bool(whiten_items)
        self._model_type = str(model_type).lower()
        self._feature_mode = str(feature_mode).lower()
        self._mmr_lambda = mmr_lambda
        self._cosine_sim = cosine_sim
        self._mmr_pool = int(mmr_pool)
        self._coherent = bool(coherent)
        self._primary_slots = int(primary_slots)
        self._wildcard_slots = int(wildcard_slots)
        self._free_slots = int(free_slots)
        self._primary_top_k = int(primary_top_k)
        self._wildcard_top_k = int(wildcard_top_k)
        self._seed = int(seed)

        # Coherent re-ranking artifacts (built lazily once we know personalities + items)
        self._item_genres: np.ndarray | None = None
        self._genre_names: list[str] | None = None
        self._user_genre_affinity: dict[int, np.ndarray] = {}
        self._movies_df = movies_df
        if self._coherent and movies_df is None:
            raise ValueError("coherent=True requires movies_df with 'movie_id' and 'genres' columns")

        if self._model_type not in {"linear", "mlp"}:
            raise ValueError(f"Unknown model_type: {self._model_type}")
        if self._feature_mode not in {"raw", "quantile", "quantile_cross"}:
            raise ValueError(f"Unknown feature_mode: {self._feature_mode}")

        self._sorted_cols: np.ndarray | None = None
        self._build_features(personalities, fit=True)

        # Frozen item embeddings: optional L2-normalization + optional ZCA whitening
        Ei = cf_item_embeddings.astype(np.float32)
        if self._whiten_items:
            self._zca_W = _zca_whitening_matrix(Ei)
            Ei = Ei @ self._zca_W
        else:
            self._zca_W = None
        if self._normalize_items:
            norms = np.linalg.norm(Ei, axis=1, keepdims=True)
            norms = np.where(norms < 1e-8, 1.0, norms)
            Ei = Ei / norms
        self._Ei = Ei
        self._n_items = self._Ei.shape[0]

        self._head = None
        self._item_bias: np.ndarray | None = None
        self._item_popularity: np.ndarray | None = None
        self._user_seen: dict[int, set[int]] = {}

        if self._coherent:
            self._item_genres, self._genre_names = build_item_genres(self._movies_df, self._n_items)
            self._build_user_genre_affinity(personalities)

    @property
    def _input_dim(self) -> int:
        if self._feature_mode == "quantile_cross":
            return len(TRAIT_COLS) + len(_CROSS_PAIRS)
        return len(TRAIT_COLS)

    def _build_features(self, personalities: pd.DataFrame, fit: bool) -> None:
        """Compute trait features per user with the configured feature_mode."""
        traits_arr = personalities[TRAIT_COLS].to_numpy(dtype=np.float32)
        if self._feature_mode == "raw":
            if fit:
                self._trait_mean = traits_arr.mean(axis=0)
                self._trait_std = traits_arr.std(axis=0).clip(1e-6)
            base = (traits_arr - self._trait_mean) / self._trait_std
            features = base.astype(np.float32)
        else:
            # quantile or quantile_cross
            if fit:
                base, self._sorted_cols = _quantile_transform(traits_arr)
            else:
                base = _apply_quantile(traits_arr, self._sorted_cols)
            if self._feature_mode == "quantile_cross":
                features = _add_cross_features(personalities, base)
            else:
                features = base
        self._traits = {
            int(uid): features[i] for i, uid in enumerate(personalities["user_id"].values)
        }

    def set_personalities(self, personalities: pd.DataFrame) -> None:
        """Swap the personality lookup without re-training."""
        self._build_features(personalities, fit=False)
        self._user_seen = {}
        if self._coherent:
            self._build_user_genre_affinity(personalities)

    def _build_user_genre_affinity(self, personalities: pd.DataFrame) -> None:
        """Compute genre affinity per user from raw (un-normalized) traits via Nave."""
        traits_arr = personalities[TRAIT_COLS].to_numpy(dtype=np.float32)
        affinity = compute_user_genre_affinity(traits_arr, self._genre_names)
        self._user_genre_affinity = {
            int(uid): affinity[i]
            for i, uid in enumerate(personalities["user_id"].values)
        }

    def _user_emb(self, traits: np.ndarray, training: bool = False,
                  rng: np.random.Generator | None = None):
        dropout = self._dropout if training and self._model_type == "mlp" else 0.0
        out, cache = self._head.forward(traits, dropout=dropout, rng=rng)
        return out, cache

    def _build_head(self) -> None:
        if self._model_type == "linear":
            self._head = _Linear(self._input_dim, self._embedding_dim, self._seed)
        else:
            self._head = _MLP(self._input_dim, self._hidden_dim, self._embedding_dim, self._seed)

    def fit(self, ratings: pd.DataFrame) -> None:
        rng = np.random.default_rng(self._seed)

        self._user_seen = {}
        for uid, mid in zip(ratings["user_id"].values, ratings["movie_idx"].values):
            self._user_seen.setdefault(int(uid), set()).add(int(mid))

        pos = ratings[ratings["rating"] >= 4.0][["user_id", "movie_idx"]].copy()
        pos = pos[pos["user_id"].isin(self._traits.keys())]
        pos = pos[pos["movie_idx"] < self._n_items].reset_index(drop=True)

        self._build_head()
        self._item_bias = np.zeros(self._n_items, dtype=np.float32)

        item_counts = np.bincount(
            ratings["movie_idx"].values.astype(np.int32), minlength=self._n_items
        ).astype(np.float32)
        log_pop = np.log1p(item_counts)
        lo, hi = log_pop.min(), log_pop.max()
        self._item_popularity = (log_pop - lo) / (hi - lo) if hi > lo else np.zeros_like(log_pop)

        if len(pos) < 10:
            return

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

        opt = _Adam(self._head.params() + [self._item_bias],
                    lr=self._lr, weight_decay=self._weight_decay)

        n_train = len(train_pos)
        best_val_loss = float("inf")
        patience_ct = 0
        best_params = None

        for epoch in range(self._n_epochs):
            perm_epoch = rng.permutation(n_train)

            for b_start in range(0, n_train, self._batch_size):
                b_idx = perm_epoch[b_start: b_start + self._batch_size]
                bs = len(b_idx)

                neg_items = rng.integers(0, self._n_items, size=bs)
                for i, bi in enumerate(b_idx):
                    if int(neg_items[i]) in seen_arr[bi]:
                        neg_items[i] = rng.integers(0, self._n_items)

                t_batch = train_traits[b_idx]
                pos_b = train_pos_items[b_idx]

                u, cache = self._user_emb(t_batch, training=True, rng=rng)
                pos_emb = self._Ei[pos_b]
                neg_emb = self._Ei[neg_items]
                pos_score = (u * pos_emb).sum(axis=1) + self._item_bias[pos_b]
                neg_score = (u * neg_emb).sum(axis=1) + self._item_bias[neg_items]
                diff = pos_score - neg_score
                sig = _sigmoid(-diff)

                d_diff = -sig / bs
                d_u = d_diff[:, None] * (pos_emb - neg_emb)
                d_bi_pos = d_diff
                d_bi_neg = -d_diff

                grads = self._head.backward(d_u, cache)

                d_bias = np.zeros_like(self._item_bias)
                np.add.at(d_bias, pos_b, d_bi_pos)
                np.add.at(d_bias, neg_items, d_bi_neg)

                opt.step(grads + [d_bias])

            neg_val = rng.integers(0, self._n_items, size=len(val_pos))
            uv, _ = self._user_emb(val_traits, training=False)
            pos_s = (uv * self._Ei[val_pos_items]).sum(axis=1) + self._item_bias[val_pos_items]
            neg_s = (uv * self._Ei[neg_val]).sum(axis=1) + self._item_bias[neg_val]
            val_loss = float(-np.log(_sigmoid(pos_s - neg_s) + 1e-12).mean())

            if val_loss < best_val_loss - 1e-4:
                best_val_loss = val_loss
                patience_ct = 0
                best_params = [p.copy() for p in self._head.params()] + [self._item_bias.copy()]
            else:
                patience_ct += 1
                if patience_ct >= self._patience:
                    break

        if best_params is not None:
            head_params = self._head.params()
            for i, p in enumerate(best_params[:-1]):
                head_params[i][:] = p
            self._item_bias[:] = best_params[-1]

    def score_all(self, user_id: int) -> np.ndarray | None:
        """
        Return raw scores per item including popularity_penalty (structural).
        MMR and bucket re-ranking live in recommend() (display only).
        """
        if self._head is None:
            return None
        traits = self._traits.get(int(user_id))
        if traits is None:
            return None
        u, _ = self._user_emb(traits[None, :], training=False)
        scores = (u @ self._Ei.T).ravel() + self._item_bias
        if self._popularity_penalty > 0.0 and self._item_popularity is not None:
            std = scores.std()
            if std > 1e-8:
                penalty = np.power(self._item_popularity, self._pop_gamma)
                scores = scores - self._popularity_penalty * std * penalty
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

        # Coherent genre-aware re-ranking takes precedence over MMR
        if self._coherent and self._item_genres is not None:
            user_aff = self._user_genre_affinity.get(int(user_id))
            if user_aff is not None:
                return coherent_rerank(
                    scores=scores,
                    item_genres=self._item_genres,
                    user_genre_affinity=user_aff,
                    n=n,
                    primary_slots=self._primary_slots,
                    wildcard_slots=self._wildcard_slots,
                    free_slots=self._free_slots,
                    pool_size=max(n, self._mmr_pool),
                    primary_top_k=self._primary_top_k,
                    wildcard_top_k=self._wildcard_top_k,
                    excluded=to_suppress,
                )

        if self._mmr_lambda is not None and self._cosine_sim is not None:
            pool = np.argsort(-scores)[:max(n, self._mmr_pool)].tolist()
            return self._mmr_rerank(pool, scores, n)
        return np.argsort(-scores)[:n].tolist()
