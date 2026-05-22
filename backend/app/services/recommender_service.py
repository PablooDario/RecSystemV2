from sqlalchemy.orm import Session
from app.models.movie_model import Movie
from app.services.recommendations.content_based import ContentService

class RecommendationService:
    def __init__(self, db: Session):
        self.db = db

    def get_content_recommendations(self, user_id: int) -> list[Movie] | None:

        content_service = ContentService(self.db)
        return content_service.content_recommendation(user_id=user_id, top_k=10)