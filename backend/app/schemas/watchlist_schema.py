from pydantic import BaseModel
from typing import List
from app.schemas.movie_schema import MovieWithoutActorsResponse


class WatchlistRequest(BaseModel):
    user_id: int
    movie_id: int


class WatchlistStatusResponse(BaseModel):
    in_watchlist: bool


class WatchlistResponse(BaseModel):
    movies: List[MovieWithoutActorsResponse]

    class Config:
        from_attributes = True
