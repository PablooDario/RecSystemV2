from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.auth_service import AuthService
from app.schemas.auth_schema import LoginRequest, LoginResponse


router = APIRouter(prefix="/auth", tags=["Authentication"])

# Authenticates a user and returns their info
@router.post("/login", response_model=LoginResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db) ):
    auth_service = AuthService(db)
    
    user = auth_service.authenticate_user(
        username=login_data.username,
        password=login_data.password
    )
    
    if not user:
        raise HTTPException(status_code=401, detail="Username o contraseña incorrectos")
    
    return LoginResponse(user_id=user.id, username=user.username)
