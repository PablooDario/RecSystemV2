from pydantic import BaseModel, Field

# Input of the questionnaire answers for registration
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    password: str = Field(..., min_length=6)

# Response after successful login
class LoginResponse(BaseModel):
    user_id: int
    username: str
    message: str = "Login exitoso"

    class Config:
        from_attributes = True