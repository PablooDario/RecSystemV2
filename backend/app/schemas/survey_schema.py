from pydantic import BaseModel


class SurveyAnswerRequest(BaseModel):
    user_id: int
    answers: dict[str, str]  # {"P1": "4", "P2": "3", "P3": "personalidad", ...}


class SurveyStatusResponse(BaseModel):
    completed: bool


class SurveyResultItem(BaseModel):
    question_id: str
    answers: list[str]
    count: int


class SurveyResultsResponse(BaseModel):
    total_responses: int
    results: dict[str, dict[str, int]]  # {"P1": {"1": 0, "2": 1, "3": 3, ...}}
