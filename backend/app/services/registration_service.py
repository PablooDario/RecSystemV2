from sqlalchemy.orm import Session
from typing import Dict
from app.services.user_service import UserService
from app.services.personality_service import PersonalityService


class RegistrationService:
    
    def __init__(self, db: Session):
        self.db = db
        self.user_service = UserService(db)
        self.personality_service = PersonalityService(db)

    def check_username_availability(self, username: str) -> bool:
        return not self.user_service.username_exists(username)

    def register_user_with_personality(
        self,
        username: str,
        password: str,
        questionnaire_answers: Dict[int, int],
        gender: str | None = None,
        age: int | None = None
    ) -> tuple[int, str, Dict[str, float]]:
        """
        Register new user with personality traits calculated from questionnaire.
        
        Process:
        1. Calculate Big Five personality traits from questionnaire
        2. Create user (password automatically hashed)
        3. Flush to get user.id
        4. Create personality record linked to user
        5. Commit entire transaction atomically
        
        Args:
            username: Desired username
            password: Plain text password
            questionnaire_answers: Dict mapping question_id to answer (1-5)
            gender: Optional gender
            age: Optional age
            
        Returns:
            Tuple of (user_id, username, personality_traits_dict)
        
        Raises:
            ValueError: Invalid questionnaire answers (wrong count or values)
            IntegrityError: Username already exists
        """
        # Calculate Big Five traits from questionnaire
        personality_traits = PersonalityService.calculate_big_five_traits(
            questionnaire_answers
        )
        
        # Create user (password hashing handled internally by UserService)
        user = self.user_service.create_user(
            username=username,
            password=password,
            gender=gender,
            age=age
        )
        
        # Flush to generate user.id without committing
        self.db.flush()
        
        # Create personality record linked to user
        self.personality_service.create_personality(
            user_id=user.id,
            traits=personality_traits
        )
        
        # Commit both user and personality together (atomic transaction)
        self.db.commit()
        self.db.refresh(user)
        
        return user.id, user.username, personality_traits