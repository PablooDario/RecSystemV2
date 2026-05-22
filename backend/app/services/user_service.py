from sqlalchemy import exists
from sqlalchemy.orm import Session, joinedload
from app.models.user_model import User
from app.models.rating_model import Rating
from app.models.movie_model import Movie
from app.services.auth_service import AuthService


class UserService:
    
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_id(self, user_id: int) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_with_personality(self, user_id: int) -> User | None:
        return (
            self.db.query(User)
            .options(joinedload(User.personality))
            .filter(User.id == user_id)
            .first()
        )

    def username_exists(self, username: str) -> bool:
        return self.db.query(
            exists().where(User.username == username.lower())
        ).scalar()

    def create_user(
        self, 
        username: str, 
        password: str,
        gender: str | None = None, 
        age: int | None = None
    ) -> User:
        """
        Create new user with hashed password.
        
        Note: Does NOT commit - caller is responsible for transaction management.
        Use db.flush() to get the user.id, then db.commit() when ready.
        
        Args:
            username: Username (will be lowercased)
            password: Plain text password (will be hashed)
            gender: Optional gender
            age: Optional age
            
        Returns:
            User object (not yet committed)
        """
        user = User(
            username=username.lower(),
            password_hash=AuthService.hash_password(password),
            gender=gender,
            age=age
        )
        
        self.db.add(user)
        return user
    
    def get_user_watched_movies(self, user_id: int) -> list[int]:
        """
        Return a list of movie IDs that the user has watched (rated)
        """
        movie_ids = self.db.query(Rating.movie_id).filter(Rating.user_id == user_id).all()
        return [movie_id for (movie_id,) in movie_ids]
    
    def get_user_watched_movies_with_details(self, user_id: int) -> list[Movie]:
        """
        Return complete movie details for all movies the user has watched (rated)
        
        Optimized: Single query with JOIN instead of N+1 queries
        """
        movies = (
            self.db.query(Movie)
            .join(Rating, Rating.movie_id == Movie.id)
            .filter(Rating.user_id == user_id)
            .order_by(Rating.timestamp.desc())
            .all()
        )
        
        return movies