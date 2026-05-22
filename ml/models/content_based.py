from pathlib import Path

import numpy as np
import pandas as pd

from .base import BaseRecommender

# A movie is considered "liked" if rated above this threshold.
POSITIVE_THRESHOLD = 3.5
# Number of top-rated movies used as seeds for the similarity average.
TOP_SEED_MOVIES = 10
# Popularity blend: final = (1-α)*content + α*popularity
POPULARITY_ALPHA = 0.10
# Adaptive pooling: content = β*max + (1-β)*mean. β=1.0 → pure max-pooling.
POOLING_BETA = 1.0
# MMR candidate pool size (top-N scores fed into the re-ranker).
MMR_CANDIDATE_POOL = 50


class ContentBasedRecommender(BaseRecommender):
    """
    Content-based recommender using a precomputed cosine similarity matrix.

    The matrix (cosine_sim.npy) was built from sentence-transformer embeddings
    (all-mpnet-base-v2) of movie features: title, genres, director, overview,
    cast, and keywords — combined as a weighted average.

    Aggregation: rating-weighted adaptive pooling (β*max + (1-β)*mean) over
    the user's top-rated seed movies, blended with a small popularity signal to
    break ties in favor of movies users are more likely to watch.

    Optional MMR re-ranking: when mmr_lambda is set, the top MMR_CANDIDATE_POOL
    candidates are re-ranked using Maximal Marginal Relevance to improve diversity.

    Matrix shape: (n_movies, n_movies), float32.
    Index 0 corresponds to the movie with movie_id=0 in movies_final.csv.
    """

    def __init__(
        self,
        cosine_sim_path: str | Path,
        movies_path: str | Path | None = None,
        cosine_sim: np.ndarray | None = None,
        positive_threshold: float = POSITIVE_THRESHOLD,
        top_seed_movies: int = TOP_SEED_MOVIES,
        popularity_alpha: float = POPULARITY_ALPHA,
        beta: float = POOLING_BETA,
        mmr_lambda: float | None = None,
    ) -> None:
        self._path = Path(cosine_sim_path)
        # Accept a pre-loaded matrix to avoid repeated 98 MB disk reads
        # when many instances are created (e.g. grid search or survey LOO folds).
        self._cosine_sim: np.ndarray | None = cosine_sim
        self._popularity: np.ndarray | None = None
        self._movies_path = movies_path
        # Populated by fit(): user_id → {movie_idx: rating}
        self._user_ratings: dict[int, dict[int, float]] = {}
        # Hyperparameters
        self._positive_threshold = positive_threshold
        self._top_seed_movies = top_seed_movies
        self._popularity_alpha = popularity_alpha
        self._beta = beta
        self._mmr_lambda = mmr_lambda

    @property
    def cosine_sim(self) -> np.ndarray:
        """Load the matrix on first access (lazy, cached)."""
        if self._cosine_sim is None:
            if not self._path.exists():
                raise FileNotFoundError(
                    f"Cosine similarity matrix not found: {self._path}"
                )
            self._cosine_sim = np.load(self._path)
        return self._cosine_sim

    @property
    def popularity(self) -> np.ndarray:
        """Min-max normalised popularity scores, indexed by movie_id."""
        if self._popularity is None:
            if self._movies_path is not None:
                mp = Path(self._movies_path)
            else:
                # Default: relative to this source file
                mp = Path(__file__).resolve().parent.parent / "data" / "processed" / "movies_final.csv"
            movies = pd.read_csv(mp, usecols=["movie_id", "score"])
            movies = movies.sort_values("movie_id")
            scores = movies["score"].to_numpy(dtype=np.float64)
            lo, hi = float(scores.min()), float(scores.max())
            self._popularity = (scores - lo) / (hi - lo) if hi > lo else np.zeros_like(scores)
        return self._popularity

    def fit(self, ratings: pd.DataFrame) -> None:
        """
        Store the training ratings for later inference.

        Args:
            ratings: DataFrame with columns [user_id, movie_idx, rating].
        """
        self._user_ratings = {}
        for row in ratings.itertuples(index=False):
            uid = int(row.user_id)
            self._user_ratings.setdefault(uid, {})[int(row.movie_idx)] = float(
                row.rating
            )

    def _get_seeds(self, user_id: int) -> list[tuple[int, float]]:
        """Top-rated positive movies for a user, validated against matrix bounds."""
        user_ratings = self._user_ratings.get(user_id, {})
        positive = sorted(
            [(idx, r) for idx, r in user_ratings.items() if r > self._positive_threshold],
            key=lambda x: x[1],
            reverse=True,
        )[:self._top_seed_movies]
        return [(idx, r) for idx, r in positive if 0 <= idx < self.cosine_sim.shape[0]]

    def _aggregate_scores(self, seeds: list[tuple[int, float]]) -> np.ndarray:
        """Rating-weighted adaptive pooling over seed similarity rows, blended with popularity."""
        indices = [idx for idx, _ in seeds]
        ratings = np.array([r for _, r in seeds])
        weights = ratings - self._positive_threshold
        weights = weights / weights.max()
        seed_sims = self.cosine_sim[indices]
        weighted = seed_sims * weights[:, np.newaxis]
        max_pool = np.max(weighted, axis=0)
        mean_pool = np.mean(weighted, axis=0)
        content = self._beta * max_pool + (1.0 - self._beta) * mean_pool
        return (1 - self._popularity_alpha) * content + self._popularity_alpha * self.popularity

    def _mmr_rerank(self, pool: list[int], scores: np.ndarray, n: int) -> list[int]:
        """
        Greedy MMR re-ranking over `pool`.

        At each step selects the item i that maximises:
            λ * relevance(i) − (1−λ) * max_sim(i, already_selected)
        """
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
                        - (1 - lam) * float(np.max(self.cosine_sim[i, selected]))
                    ),
                )
            selected.append(best)
            remaining.remove(best)
        return selected

    def recommend(
        self,
        user_id: int,
        n: int = 10,
        exclude: set[int] | None = None,
    ) -> list[int]:
        seeds = self._get_seeds(user_id)
        if not seeds:
            return []

        sim_scores = self._aggregate_scores(seeds)

        # Suppress seen movies and any explicitly excluded indices
        to_suppress = set(self._user_ratings.get(user_id, {}).keys())
        if exclude:
            to_suppress |= exclude
        for idx in to_suppress:
            if 0 <= idx < len(sim_scores):
                sim_scores[idx] = -1.0

        if self._mmr_lambda is not None:
            pool = np.argsort(sim_scores)[::-1][:max(n, MMR_CANDIDATE_POOL)].tolist()
            return self._mmr_rerank(pool, sim_scores, n)
        return np.argsort(sim_scores)[::-1][:n].tolist()

    def score_all(self, user_id: int) -> np.ndarray | None:
        """
        Return the per-movie similarity score for every catalog item, or None
        if the user has no positive ratings to seed the average.

        Note: score_all() always uses the raw aggregated scores without MMR,
        as it is used by the survey evaluation protocol (full-catalog ranking).
        """
        seeds = self._get_seeds(user_id)
        if not seeds:
            return None
        return self._aggregate_scores(seeds)
