from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.schemas.personality_schema import PersonalityTraits

class UserResponse(BaseModel):
    id: int
    username: str
    gender: Optional[str] = None
    age: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    id: int
    username: str
    gender: Optional[str] = None
    age: Optional[int] = None
    created_at: datetime
    personality: Optional[PersonalityTraits] = None

    class Config:
        from_attributes = True