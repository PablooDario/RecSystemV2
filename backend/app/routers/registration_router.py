from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.services.registration_service import RegistrationService
from app.schemas.registration_schema import (
    UserRegistrationRequest,
    UsernameCheckRequest,
    UsernameCheckResponse,
    RegistrationResponse
)


router = APIRouter(prefix="/registration", tags=["Registration"])


@router.post("/check-username", response_model=UsernameCheckResponse)
def check_username(request: UsernameCheckRequest, db: Session = Depends(get_db)):
    registration_service = RegistrationService(db)
    is_available = registration_service.check_username_availability(request.username)
    
    return UsernameCheckResponse(username=request.username.lower(), available=is_available)


@router.post("/register", response_model=RegistrationResponse, status_code=201)
def register_user(registration_data: UserRegistrationRequest, db: Session = Depends(get_db) ):
    """
    Registra un nuevo usuario junto con sus rasgos de personalidad.
    
    Este endpoint:
    1. Valida los datos de registro y las respuestas del cuestionario
    2. Calcula los 5 rasgos de personalidad (Big Five)
    3. Crea el usuario en la base de datos
    4. Guarda los rasgos de personalidad
    5. Retorna los datos del usuario y sus rasgos
    
    Todo ocurre en una transacción atómica: si algo falla, nada se guarda.
    """
    registration_service = RegistrationService(db)
    
    try:
        user_id, username, personality_traits = registration_service.register_user_with_personality(
            username=registration_data.username,
            password=registration_data.password,
            questionnaire_answers=registration_data.questionnaire_answers.answers,
            gender=registration_data.gender,
            age=registration_data.age
        )
        
        return RegistrationResponse(
            user_id=user_id,
            username=username,
            personality_traits=personality_traits
        )
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El username '{registration_data.username}' ya está en uso"
        )
    
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}"
        )