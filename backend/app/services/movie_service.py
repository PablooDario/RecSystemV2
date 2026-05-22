import  re
import random
from sqlalchemy.orm import Session, joinedload
from app.models import Movie, Actor, MovieActor


class MovieService:
    def __init__(self, db: Session):
        self.db = db


    def get_movie_by_id(self, movie_id: int) -> dict | None:
        # Movie with its actors using joinedload
        movie = (
            self.db.query(Movie)
            .options(joinedload(Movie.actors).joinedload(MovieActor.actor))
            .filter(Movie.id == movie_id)
            .first()
        )

        if not movie:
            return None

        return {
            "id": movie.id,
            "tmdb_id": movie.tmdb_id,
            "title": movie.title,
            "genres": movie.genres,
            "overview": movie.overview,
            "release_date": movie.release_date,
            "vote_average": movie.vote_average,
            "vote_count": movie.vote_count,
            "runtime": movie.runtime,
            "tagline": movie.tagline,
            "director": movie.director,
            "poster_path": movie.poster_path,
            "backdrop_path": movie.backdrop_path,
            "actors": [
                {
                    "id": ma.actor.id,
                    "tmdb_id": ma.actor.tmdb_id,
                    "name": ma.actor.name,
                    "profile_path": ma.actor.profile_path
                }
                for ma in movie.actors
            ]
        }


    def get_popular_movies(self) -> list[Movie]:
        movies = (
            self.db.query(Movie)
            .where(Movie.vote_count >= 10000)
            .order_by(Movie.vote_average.desc())
            .limit(50)
            .all()
        )
        
        return random.sample(movies, 20)

    def search_movies(self, query: str) -> list[Movie] | None:
        query = query.strip() # Remove extra spaces at the beginning and end
        query = re.sub(r'\s+', ' ', query) # Replace multiple spaces with a single space

        return (
            self.db.query(Movie)
            .filter(Movie.title.ilike(f"%{query}%"))  # Incase sensitive
            .order_by(Movie.vote_count.desc())
            .limit(20)
            .all()
        )
