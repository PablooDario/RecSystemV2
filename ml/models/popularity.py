"""
Popularity-based recommender (non-personalised baseline).

Recommends the same top-scored movies to every user, excluding
items the user has already rated. Popularity is determined by the
``score`` column in movies_final.csv (a pre-computed weighted rating).
"""

import pickle
from pathlib import Path

import numpy as np
import pandas as pd

from .base import BaseRecommender


class PopularityRecommender(BaseRecommender):
    """
    Baseline recommender that returns the most popular movies.

    Parameters
    ----------
    movies_path : str | Path
        Path to movies_final.csv (must contain ``movie_id`` and ``score``).
    """

    def __init__(self, movies_path: str | Path) -> None:
        movies = pd.read_csv(movies_path, usecols=["movie_id", "score"])
        movies = movies.sort_values("score", ascending=False)
        # Ordered list of movie indices (0-based) from most to least popular
        self._ranking: list[int] = movies["movie_id"].tolist()
        # Per-movie popularity score, indexed by movie_id (0-based matrix index)
        movies_sorted = movies.sort_values("movie_id")
        self._scores = movies_sorted["score"].to_numpy(dtype=np.float32)
        self._seen: dict[int, set[int]] = {}

    def fit(self, ratings: pd.DataFrame) -> None:
        """Store which movies each user has already rated."""
        self._seen = (
            ratings.groupby("user_id")["movie_idx"]
            .apply(set)
            .to_dict()
        )

    def recommend(
        self,
        user_id: int,
        n: int = 10,
        exclude: set[int] | None = None,
    ) -> list[int]:
        seen = self._seen.get(user_id, set())
        if exclude:
            seen = seen | exclude

        recs: list[int] = []
        for movie_idx in self._ranking:
            if movie_idx not in seen:
                recs.append(movie_idx)
            if len(recs) >= n:
                break
        return recs

    def score_all(self, user_id: int) -> np.ndarray:
        """Same popularity score for every user (non-personalised)."""
        return self._scores.copy()

    def save(self, path: str | Path) -> None:
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path: str | Path) -> "PopularityRecommender":
        with open(path, "rb") as f:
            return pickle.load(f)
