from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.models.user_model import User

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    # Handles authentication logic and password operations
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def hash_password(password: str) -> str:
        # Hash a plain-text password using bcrypt
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        # Check a plain password against its hashed version
        return pwd_context.verify(plain_password, hashed_password)

    def authenticate_user(self, username: str, password: str) -> User | None:
        """
        Authenticate a user by username and password.

        Returns:
            User object if credentials are correct, None otherwise
        """
        
        # Query the user by username (case-insensitive)
        user = self.db.query(User).filter(
            User.username == username.lower()
        ).first()
        
        if not user:
            return None

        # Verify password matches the stored hash
        if not self.verify_password(password, user.password_hash):
            return None
        
        return user
