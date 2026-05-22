from sqlalchemy.orm import Session
from app.models.rating_model import Rating
from app.models.movie_model import Movie
from app.models.user_model import User


class RatingService:
    def __init__(self, db: Session):
        self.db = db

    def create_or_update_rating(self, user_id: int, movie_id: int, rating_value: float) -> Rating:

        # Check user exists
        if not self.db.get(User, user_id):
            raise ValueError("User not found")

        # Check movie exists
        if not self.db.get(Movie, movie_id):
            raise ValueError("Movie not found")

        # Get existing rating (composite PK)
        rating = self.db.get(Rating, (user_id, movie_id))

        if rating:
            rating.rating = rating_value  # Update
        else:
            rating = Rating( # Create new
                user_id=user_id,
                movie_id=movie_id,
                rating=rating_value
            )
            self.db.add(rating)

        self.db.commit()
        self.db.refresh(rating)

        return rating

    def get_user_rating(self, user_id: int, movie_id: int) -> Rating | None:
        return self.db.get(Rating, (user_id, movie_id))
