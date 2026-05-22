from pydantic import BaseModel, Field

class RatingRequest(BaseModel):
    user_id: int
    movie_id: int
    rating: float = Field(..., ge=0.5, le=5.0)


class RatingResponse(BaseModel):
    user_id: int
    movie_id: int
    rating: float
    
    class Config:
        from_attributes = True