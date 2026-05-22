from pydantic import BaseModel
from datetime import date
from typing import Optional, List
from app.schemas.actor_schema import ActorResponse


class MovieResponse(BaseModel):
    id: int
    tmdb_id: Optional[int] = None
    title: str
    genres: Optional[List[str]] = None
    overview: Optional[str] = None
    release_date: Optional[date] = None
    vote_average: Optional[float] = None
    vote_count: Optional[int] = None
    runtime: Optional[int] = None
    tagline: Optional[str] = None
    director: Optional[str] = None
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    actors: Optional[List[ActorResponse]] = None

    class Config:
        from_attributes = True

class MovieWithoutActorsResponse(BaseModel):
    id: int
    tmdb_id: Optional[int] = None
    title: str
    genres: Optional[List[str]] = None
    overview: Optional[str] = None
    release_date: Optional[date] = None
    vote_average: Optional[float] = None
    vote_count: Optional[int] = None
    runtime: Optional[int] = None
    tagline: Optional[str] = None
    director: Optional[str] = None
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None

    class Config:
        from_attributes = True


class RecommendationSection(BaseModel):
    title: str
    model: str
    movies: List[MovieWithoutActorsResponse]

    class Config:
        from_attributes = True


class RecommendationResponse(BaseModel):
    sections: List[RecommendationSection]
    rating_count: int
    next_threshold: Optional[int] = None
    next_model: Optional[str] = None

    class Config:
        from_attributes = True