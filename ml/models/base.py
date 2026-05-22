from abc import ABC, abstractmethod

import numpy as np
import pandas as pd


class BaseRecommender(ABC):
    """
    Abstract interface for all recommender models.

    Every model receives a ratings DataFrame (user_id, movie_idx, rating)
    where movie_idx is the 0-based index into the cosine similarity matrix.
    It must return a ranked list of movie indices (0-based, best first).
    """

    @abstractmethod
    def fit(self, ratings: pd.DataFrame) -> None:
        """
        Prepare the model from training ratings.

        Args:
            ratings: DataFrame with columns [user_id, movie_idx, rating].
        """
        ...

    @abstractmethod
    def recommend(
        self,
        user_id: int,
        n: int = 10,
        exclude: set[int] | None = None,
    ) -> list[int]:
        """
        Return the top-n recommended movie indices for a user.

        Args:
            user_id: User identifier (must have been seen during fit).
            n: Number of recommendations to return.
            exclude: Additional movie indices to suppress (e.g. already seen).

        Returns:
            List of 0-based matrix indices, sorted by relevance descending.
            Returns an empty list if the user cannot be served.
        """
        ...

    def score_all(self, user_id: int) -> np.ndarray | None:
        """
        Return the raw score for every movie in the catalog as a 1-D array.

        Higher scores mean stronger preference. Used by the sampled-evaluation
        protocol to rank a small candidate set without re-running ``recommend``.
        Models that cannot serve the user (cold start) should return ``None``.
        Override in concrete recommenders.
        """
        return None
