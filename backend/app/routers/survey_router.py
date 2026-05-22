from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.survey_service import SurveyService
from app.schemas.survey_schema import SurveyAnswerRequest, SurveyStatusResponse

router = APIRouter(prefix="/survey", tags=["Survey"])


@router.get("/status/{user_id}", response_model=SurveyStatusResponse)
def get_survey_status(user_id: int, db: Session = Depends(get_db)):
    service = SurveyService(db)
    return {"completed": service.has_completed(user_id)}


@router.post("/submit")
def submit_survey(data: SurveyAnswerRequest, db: Session = Depends(get_db)):
    service = SurveyService(db)
    service.submit_answers(data.user_id, data.answers)
    return {"message": "Encuesta enviada correctamente"}


@router.get("/results")
def get_survey_results(db: Session = Depends(get_db)):
    service = SurveyService(db)
    return service.get_results()
