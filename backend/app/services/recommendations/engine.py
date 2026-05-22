from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Movie, Rating, Personality
from app.services.recommendations.model_loader import get_n_items
from app.services.recommendations.personality_recommender import personality_recommend
from app.services.recommendations.content_based import ContentService
from app.services.recommendations.cf_recommender import cf_recommend
from app.services.recommendations.hybrid_recommender import hybrid_recommend

THRESHOLD_CONTENT = 1
THRESHOLD_CF = 10
THRESHOLD_HYBRID = 15
POSITIVE_THRESHOLD = 3.5

SECTION_TITLES = {
    "personality": "Recomendaciones basadas en tu personalidad",
    "content_based": "Peliculas similares a las que te gustaron",
    "collaborative": "Recomendaciones basadas en personas con gustos similares",
    "hybrid": "Recomendaciones pensadas en ti",
}


class RecommendationEngine:
    def __init__(self, db: Session) -> None:
        self.db = db

    def recommend(self, user_id: int, top_k: int = 10) -> dict:
        total_ratings = (
            self.db.query(func.count(Rating.movie_id))
            .filter(Rating.user_id == user_id)
            .scalar()
        )

        positive_count = (
            self.db.query(func.count(Rating.movie_id))
            .filter(Rating.user_id == user_id, Rating.rating >= POSITIVE_THRESHOLD)
            .scalar()
        )

        personality = (
            self.db.query(Personality)
            .filter(Personality.user_id == user_id)
            .first()
        )

        if personality is None:
            raise ValueError(f"User {user_id} has no personality data")

        traits = {
            "openness": float(personality.openness),
            "conscientiousness": float(personality.conscientiousness),
            "extraversion": float(personality.extraversion),
            "agreeableness": float(personality.agreeableness),
            "neuroticism": float(personality.neuroticism),
        }

        exclude = self._get_watched_indices(user_id)
        user_ratings = self._get_user_ratings(user_id)

        sections = []

        sections.append(self._build_section(
            "personality", personality_recommend(traits, exclude, top_k)
        ))

        if positive_count >= THRESHOLD_CONTENT:
            content_indices = self._content_recommend(user_id, top_k)
            if content_indices:
                sections.append(self._build_section("content_based", content_indices))

        if total_ratings >= THRESHOLD_CF:
            cf_indices = cf_recommend(user_ratings, exclude, top_k)
            if cf_indices:
                sections.append(self._build_section("collaborative", cf_indices))

        if total_ratings >= THRESHOLD_HYBRID:
            hybrid_indices = hybrid_recommend(user_ratings, traits, exclude, top_k)
            if hybrid_indices:
                sections.append(self._build_section("hybrid", hybrid_indices))

        next_threshold, next_model = self._next_unlock(total_ratings, positive_count)

        return {
            "sections": sections,
            "rating_count": total_ratings,
            "next_threshold": next_threshold,
            "next_model": next_model,
        }

    def _build_section(self, model: str, indices: list[int]) -> dict:
        movie_ids = [idx + 1 for idx in indices]
        movies = (
            self.db.query(Movie)
            .filter(Movie.id.in_(movie_ids))
            .all()
        )
        id_to_movie = {m.id: m for m in movies}
        ordered_movies = [id_to_movie[mid] for mid in movie_ids if mid in id_to_movie]

        return {
            "title": SECTION_TITLES[model],
            "model": model,
            "movies": ordered_movies,
        }

    def _next_unlock(
        self, total_ratings: int, positive_count: int
    ) -> tuple[int | None, str | None]:
        if total_ratings >= THRESHOLD_HYBRID:
            return None, None
        if total_ratings >= THRESHOLD_CF:
            return THRESHOLD_HYBRID, "hybrid"
        if positive_count >= THRESHOLD_CONTENT:
            return THRESHOLD_CF, "collaborative"
        return THRESHOLD_CONTENT, "content_based"

    def _get_watched_indices(self, user_id: int) -> set[int]:
        watched = (
            self.db.query(Rating.movie_id)
            .filter(Rating.user_id == user_id)
            .all()
        )
        return {movie_id - 1 for (movie_id,) in watched}

    def _get_user_ratings(self, user_id: int) -> dict[int, float]:
        ratings = (
            self.db.query(Rating.movie_id, Rating.rating)
            .filter(Rating.user_id == user_id)
            .all()
        )
        return {movie_id - 1: float(rating) for movie_id, rating in ratings}

    def _content_recommend(self, user_id: int, top_k: int) -> list[int]:
        service = ContentService(self.db)
        movies = service.content_recommendation(user_id, top_k)
        if not movies:
            return []
        return [m.id - 1 for m in movies]
