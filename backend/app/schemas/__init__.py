from app.schemas.movie_schema import MovieResponse, MovieWithoutActorsResponse
from app.schemas.actor_schema import ActorResponse
from app.schemas.user_schema import UserResponse, UserProfileResponse
from app.schemas.auth_schema import LoginRequest, LoginResponse
from app.schemas.personality_schema import PersonalityTraits, PersonalityResponse
from app.schemas.registration_schema import (UserRegistrationRequest, RegistrationResponse, 
    QuestionnaireAnswers, UsernameCheckRequest, UsernameCheckResponse
)
from app.schemas.rating_schema import RatingRequest, RatingResponse