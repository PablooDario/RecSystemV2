from pydantic import BaseModel, Field
from typing import Optional

# Input of the questionnaire answers for registration
class PersonalityTraits(BaseModel):
    openness: float = Field(..., ge=1.0, le=5.0)
    conscientiousness: float = Field(..., ge=1.0, le=5.0)
    extraversion: float = Field(..., ge=1.0, le=5.0)
    agreeableness: float = Field(..., ge=1.0, le=5.0)
    neuroticism: float = Field(..., ge=1.0, le=5.0)

    class Config:
        from_attributes = True

# Output of the personality traits when queried
class PersonalityResponse(BaseModel):
    user_id: int
    openness: float
    conscientiousness: float
    extraversion: float
    agreeableness: float
    neuroticism: float

    class Config:
        from_attributes = True