from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.user_service import UserService
from app.schemas.user_schema import UserResponse, UserProfileResponse
from app.schemas.movie_schema import MovieWithoutActorsResponse


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return user


@router.get("/{user_id}/profile", response_model=UserProfileResponse)
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    user_service = UserService(db)
    user = user_service.get_user_with_personality(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return user

    
@router.get("/{user_id}/watched", response_model=list[int])
def get_user_watched_movies(user_id: int, db: Session = Depends(get_db)):
    """
    Returns only movie IDs (kept for backwards compatibility)
    """
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    watched_movies = user_service.get_user_watched_movies(user_id)
    return watched_movies


@router.get("/{user_id}/watched-movies", response_model=list[MovieWithoutActorsResponse])
def get_user_watched_movies_with_details(user_id: int, db: Session = Depends(get_db)):
    """
    Returns complete movie details for watched movies (OPTIMIZED)
    
    Uses a single JOIN query instead of N+1 individual queries
    """
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    watched_movies = user_service.get_user_watched_movies_with_details(user_id)
    return watched_movies