from pydantic import BaseModel, Field, field_validator
from typing import Dict, Optional


class QuestionnaireAnswers(BaseModel):
    # Represents the user's answers to the questionnaire (question_id -> answer)
    answers: Dict[int, int]
    
    @field_validator('answers')  # Validate 'answers' field when model is created
    @classmethod
    def validate_answers(cls, v):
        # Ensure there are exactly 30 answers
        if len(v) != 30:
            raise ValueError(f"Expected 30 answers, got {len(v)}")
        
        # Validate question IDs are between 1 and 30
        for question_id in v.keys():
            if question_id < 1 or question_id > 30:
                raise ValueError(f"Invalid question ID: {question_id}")
        
        # Validate each answer is between 1 and 5
        for question_id, answer in v.items():
            if answer < 1 or answer > 5:
                raise ValueError(
                    f"Invalid answer for question {question_id}: {answer}. "
                    "Must be between 1 and 5"
                )
        
        return v


class UserRegistrationRequest(BaseModel):
    # Request body for user registration including questionnaire answers
    username: str = Field(..., min_length=3, max_length=32)
    password: str = Field(..., min_length=6)
    gender: Optional[str] = Field(None, max_length=16)
    age: Optional[int] = Field(None, ge=13, le=120)
    questionnaire_answers: QuestionnaireAnswers
    
    @field_validator('username')  # Validate 'username' field when model is created
    @classmethod
    def validate_username(cls, v):
        # Only allow letters, numbers, underscores
        if not v.replace('_', '').isalnum():
            raise ValueError("Only letters, numbers, and underscores allowed")
        return v.lower()  # Convert username to lowercase


class UsernameCheckRequest(BaseModel):
    # Request body to check if a username is available
    username: str = Field(..., min_length=3, max_length=32)


class UsernameCheckResponse(BaseModel):
    # Response for username availability check
    username: str
    available: bool


class RegistrationResponse(BaseModel):
    # Response after successful registration
    user_id: int
    username: str
    personality_traits: dict
    message: str = "User registered successfully"

    class Config:
        # Allows creating the schema from ORM objects or attribute-style objects
        from_attributes = True
