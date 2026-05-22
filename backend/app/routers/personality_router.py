from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.personality_service import PersonalityService
from app.schemas.registration_schema import QuestionnaireAnswers
from app.schemas.personality_schema import PersonalityResponse

router = APIRouter(prefix="/personality", tags=["Personality"])


@router.put("/{user_id}", response_model=PersonalityResponse)
def update_personality(user_id: int, data: QuestionnaireAnswers, db: Session = Depends(get_db)):
    service = PersonalityService(db)
    try:
        traits = service.update_personality(user_id, data.answers)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"user_id": user_id, **traits}


@router.get("/{user_id}", response_model=PersonalityResponse)
def get_personality(user_id: int, db: Session = Depends(get_db)):
    service = PersonalityService(db)
    personality = service.get_personality_by_user_id(user_id)
    if not personality:
        raise HTTPException(status_code=404, detail=f"No personality found for user {user_id}")
    return {
        "user_id": personality.user_id,
        "openness": float(personality.openness),
        "conscientiousness": float(personality.conscientiousness),
        "extraversion": float(personality.extraversion),
        "agreeableness": float(personality.agreeableness),
        "neuroticism": float(personality.neuroticism),
    }
