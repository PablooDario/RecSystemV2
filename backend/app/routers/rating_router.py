from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.rating_service import RatingService
from app.schemas.rating_schema import RatingRequest, RatingResponse


router = APIRouter(prefix="/ratings", tags=["Ratings"])


@router.post("/", response_model=RatingResponse, status_code=201)
def create_or_update_rating(rating_data: RatingRequest, db: Session = Depends(get_db)):
    service = RatingService(db)

    try:
        return service.create_or_update_rating(
            user_id=rating_data.user_id,
            movie_id=rating_data.movie_id,
            rating_value=rating_data.rating
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{user_id}/{movie_id}", response_model=RatingResponse)
def get_user_rating(user_id: int, movie_id: int, db: Session = Depends(get_db) ):
    service = RatingService(db)

    rating = service.get_user_rating(user_id, movie_id)

    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")

    return rating
