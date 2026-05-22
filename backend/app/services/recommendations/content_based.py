import numpy as np
from sqlalchemy.orm import Session

from app.models import Movie, Rating
from app.services.recommendations.model_loader import _get_cosine_sim, _get_popularity

POSITIVE_THRESHOLD = 3.5
TOP_POSITIVE_MOVIES = 10
POPULARITY_ALPHA = 0.10


def _movie_id_to_index(movie_id: int) -> int:
    """
    Convert a database movie ID to the 0-based cosine similarity matrix index.

    The movies table was seeded in the same order as movies_final.csv, so
    database IDs are sequential starting from 1.  The matrix index is simply
    movie_id - 1.

    IMPORTANT: this assumption holds as long as the database is seeded from
    the CSV without gaps.  If you re-seed or migrate, verify this mapping.
    """
    return movie_id - 1


class ContentService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def content_recommendation(
        self, user_id: int, top_k: int = 10
    ) -> list[Movie] | None:
        """
        Return top_k recommended movies based on content similarity.

        Uses rating-weighted max-pooling over the user's top-rated seeds,
        blended with a small popularity signal (α=0.10).

        Returns None if the user has no qualifying positive ratings.
        """
        cosine_sim = _get_cosine_sim()
        pop = _get_popularity()
        n_movies = cosine_sim.shape[0]

        positive_movies = (
            self.db.query(Rating.movie_id, Rating.rating)
            .filter(
                Rating.user_id == user_id,
                Rating.rating > POSITIVE_THRESHOLD,
            )
            .order_by(Rating.rating.desc())
            .limit(TOP_POSITIVE_MOVIES)
            .all()
        )

        if not positive_movies:
            return None

        seeds = [
            (_movie_id_to_index(mid), float(r))
            for mid, r in positive_movies
            if 0 <= _movie_id_to_index(mid) < n_movies
        ]

        if not seeds:
            return None

        # Rating-weighted max-pooling + popularity blend
        indices = [idx for idx, _ in seeds]
        ratings = np.array([r for _, r in seeds])
        weights = ratings - POSITIVE_THRESHOLD
        weights = weights / weights.max()
        seed_sims = cosine_sim[indices]
        content = np.max(seed_sims * weights[:, np.newaxis], axis=0)
        sim_scores = (1 - POPULARITY_ALPHA) * content + POPULARITY_ALPHA * pop

        # Suppress already-watched movies
        watched_movies = (
            self.db.query(Rating.movie_id)
            .filter(Rating.user_id == user_id)
            .all()
        )

        for (movie_id,) in watched_movies:
            idx = _movie_id_to_index(movie_id)
            if 0 <= idx < n_movies:
                sim_scores[idx] = -1.0

        recommended_indices = np.argsort(sim_scores)[::-1][:top_k]
        recommended_ids = [idx + 1 for idx in recommended_indices]

        return (
            self.db.query(Movie)
            .filter(Movie.id.in_(recommended_ids))
            .all()
        )
