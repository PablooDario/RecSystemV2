from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.survey_model import SurveyResponse


class SurveyService:
    def __init__(self, db: Session):
        self.db = db

    def has_completed(self, user_id: int) -> bool:
        count = (
            self.db.query(func.count(SurveyResponse.id))
            .filter(SurveyResponse.user_id == user_id)
            .scalar()
        )
        return count > 0

    def submit_answers(self, user_id: int, answers: dict[str, str]) -> None:
        for question_id, answer in answers.items():
            response = SurveyResponse(
                user_id=user_id,
                question_id=question_id,
                answer=answer
            )
            self.db.merge(response)
        self.db.commit()

    def get_results(self) -> dict:
        responses = self.db.query(SurveyResponse).all()

        # Count unique users who completed
        user_ids = set(r.user_id for r in responses)

        # Aggregate by question
        results = {}
        for r in responses:
            if r.question_id not in results:
                results[r.question_id] = {}
            answer = r.answer
            results[r.question_id][answer] = results[r.question_id].get(answer, 0) + 1

        return {
            "total_responses": len(user_ids),
            "results": results
        }
