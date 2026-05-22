"""
BPR-MF — Bayesian Personalized Ranking via matrix factorization.

Wraps the `implicit` library's BPR implementation (Cython + multi-threaded)
behind the BaseRecommender interface.

Unlike SVD/SVD++, BPR-MF is trained with a pairwise ranking loss:

    L = -Σ ln σ(score(u, pos) - score(u, neg))

which directly optimizes "positive ranked higher than negative", the actual
objective of top-K recommendation. Ratings are binarized (≥ threshold → 1)
because BPR treats feedback as implicit.

Reference: Rendle et al. (2009), "BPR: Bayesian Personalized Ranking from
Implicit Feedback", UAI 2009.
"""

import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

import implicit

from .base import BaseRecommender


class BPRMF(BaseRecommender):
    """
    BPR-MF recommender (via `implicit` library).

    Parameters
    ----------
    n_factors : int
        Latent factor dimensionality.
    n_epochs : int
        Training iterations.
    lr : float
        Learning rate (SGD step size).
    reg : float
        L2 regularization on user and item factors.
    positive_threshold : float
        Ratings ≥ this value are treated as positive interactions.
    seed : int
        RNG seed for reproducibility.
    """

    def __init__(
        self,
        n_factors: int = 64,
        n_epochs: int = 100,
        lr: float = 0.01,
        reg: float = 0.01,
        positive_threshold: float = 4.0,
        seed: int = 42,
    ) -> None:
        self.n_factors = n_factors
        self.n_epochs = n_epochs
        self.lr = lr
        self.reg = reg
        self.positive_threshold = positive_threshold
        self.seed = seed

    def fit(self, ratings: pd.DataFrame) -> "BPRMF":
        """Fit on positive interactions (rating >= positive_threshold)."""
        positives = ratings[ratings["rating"] >= self.positive_threshold]
        if len(positives) == 0:
            raise ValueError(
                f"No positive ratings (>= {self.positive_threshold}) in training data"
            )

        n_users = int(ratings["user_id"].max()) + 1
        n_items = int(ratings["movie_idx"].max()) + 1
        self._n_users = n_users
        self._n_items = n_items

        # Sparse user × item matrix (binary) — `implicit`'s BPR ignores the
        # cell value and treats any non-zero entry as a positive sample.
        # (Confirmed in implicit/gpu/bpr.py: "BPR ignores the weight value
        # of the matrix right now - it treats non zero entries as a positive
        # sample".)  If you want rating-weighted confidence, use ALS instead
        # of BPR (implicit.als.AlternatingLeastSquares).
        self._matrix = csr_matrix(
            (
                np.ones(len(positives), dtype=np.float32),
                (positives["user_id"].values, positives["movie_idx"].values),
            ),
            shape=(n_users, n_items),
        )

        # Cache ALL ratings' seen items (not just positives) for recommend() filtering
        self._seen: dict[int, set[int]] = (
            ratings.groupby("user_id")["movie_idx"].apply(set).to_dict()
        )

        self._algo = implicit.bpr.BayesianPersonalizedRanking(
            factors=self.n_factors,
            learning_rate=self.lr,
            regularization=self.reg,
            iterations=self.n_epochs,
            random_state=self.seed,
            use_gpu=False,
            verify_negative_samples=True,
        )
        self._algo.fit(self._matrix, show_progress=False)

        # Precompute all scores for fast inference.
        # `implicit` adds a bias column, so factors shape is (n, n_factors+1).
        self._all_scores = (self._algo.user_factors @ self._algo.item_factors.T).astype(
            np.float32
        )
        return self

    def recommend(
        self, user_id: int, n: int = 10, exclude: set[int] | None = None
    ) -> list[int]:
        if user_id < 0 or user_id >= self._n_users:
            return []
        scores = self._all_scores[user_id].copy()
        seen = self._seen.get(user_id, set())
        if exclude:
            seen = seen | exclude
        for idx in seen:
            if 0 <= idx < len(scores):
                scores[idx] = -np.inf
        return np.argsort(scores)[::-1][:n].tolist()

    def score_all(self, user_id: int) -> np.ndarray | None:
        if user_id < 0 or user_id >= self._n_users:
            return None
        return self._all_scores[user_id]

    def save(self, path: str | Path) -> None:
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path: str | Path) -> "BPRMF":
        with open(path, "rb") as f:
            return pickle.load(f)
