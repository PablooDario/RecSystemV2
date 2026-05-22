from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.watchlist_service import WatchlistService
from app.schemas.watchlist_schema import WatchlistRequest, WatchlistResponse, WatchlistStatusResponse

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])


@router.post("/", status_code=201)
def add_to_watchlist(data: WatchlistRequest, db: Session = Depends(get_db)):
    service = WatchlistService(db)
    try:
        service.add_movie(data.user_id, data.movie_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"message": "Movie added to watchlist"}


@router.delete("/")
def remove_from_watchlist(data: WatchlistRequest, db: Session = Depends(get_db)):
    service = WatchlistService(db)
    removed = service.remove_movie(data.user_id, data.movie_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Movie not in watchlist")
    return {"message": "Movie removed from watchlist"}


@router.get("/{user_id}", response_model=WatchlistResponse)
def get_watchlist(user_id: int, db: Session = Depends(get_db)):
    service = WatchlistService(db)
    movies = service.get_watchlist(user_id)
    return {"movies": movies}


@router.get("/{user_id}/{movie_id}", response_model=WatchlistStatusResponse)
def check_watchlist(user_id: int, movie_id: int, db: Session = Depends(get_db)):
    service = WatchlistService(db)
    return {"in_watchlist": service.is_in_watchlist(user_id, movie_id)}
