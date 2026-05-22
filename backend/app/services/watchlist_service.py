from sqlalchemy.orm import Session

from app.models import Watchlist, Movie, User


class WatchlistService:
    def __init__(self, db: Session):
        self.db = db

    def add_movie(self, user_id: int, movie_id: int) -> Watchlist:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        movie = self.db.query(Movie).filter(Movie.id == movie_id).first()
        if not movie:
            raise ValueError(f"Movie {movie_id} not found")

        existing = self.db.get(Watchlist, (user_id, movie_id))
        if existing:
            return existing

        entry = Watchlist(user_id=user_id, movie_id=movie_id)
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def remove_movie(self, user_id: int, movie_id: int) -> bool:
        entry = self.db.get(Watchlist, (user_id, movie_id))
        if not entry:
            return False
        self.db.delete(entry)
        self.db.commit()
        return True

    def get_watchlist(self, user_id: int) -> list[Movie]:
        entries = (
            self.db.query(Watchlist)
            .filter(Watchlist.user_id == user_id)
            .order_by(Watchlist.added_at.desc())
            .all()
        )
        movie_ids = [e.movie_id for e in entries]
        if not movie_ids:
            return []
        movies = self.db.query(Movie).filter(Movie.id.in_(movie_ids)).all()
        id_to_movie = {m.id: m for m in movies}
        return [id_to_movie[mid] for mid in movie_ids if mid in id_to_movie]

    def is_in_watchlist(self, user_id: int, movie_id: int) -> bool:
        return self.db.get(Watchlist, (user_id, movie_id)) is not None
