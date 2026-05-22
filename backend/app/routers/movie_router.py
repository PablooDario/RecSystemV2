from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.movie_service import MovieService
from app.db.session import get_db
from app.schemas.movie_schema import MovieResponse, MovieWithoutActorsResponse

router = APIRouter(prefix="/movies", tags=["movies"])


@router.get("/", response_model=list[MovieWithoutActorsResponse])
def read_popular_movies(db: Session = Depends(get_db)):
    movie_service = MovieService(db)
    return movie_service.get_popular_movies()


@router.get("/{movie_id}", response_model=MovieResponse)
def read_movie(movie_id: int, db: Session = Depends(get_db)):
    movie_service = MovieService(db)
    movie = movie_service.get_movie_by_id(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


@router.get("/search/", response_model=list[MovieWithoutActorsResponse])
def search_movies(query: str, db: Session = Depends(get_db)):
    try:
        movie_service = MovieService(db)
        return movie_service.search_movies(query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
