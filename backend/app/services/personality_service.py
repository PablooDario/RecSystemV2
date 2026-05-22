from typing import Dict
from sqlalchemy.orm import Session
from app.models.personality_model import Personality


TRAIT_MAPPING = {
    'extraversion': {
        'normal': [7, 10, 16],
        'reversed': [5, 24, 28]
    },
    'agreeableness': {
        'normal': [1, 3, 14],
        'reversed': [22, 29, 30]
    },
    'conscientiousness': {
        'normal': [4, 9, 11],
        'reversed': [17, 23, 25]
    },
    'neuroticism': {
        'normal': [12, 21, 27],
        'reversed': [2, 8, 19]
    },
    'openness': {
        'normal': [6, 15, 20],
        'reversed': [13, 18, 26]
    }
}


class PersonalityService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def calculate_trait_score(answers: Dict[int, int], normal: list[int], reversed: list[int] ) -> float:
        scores = []
        
        for q_id in normal:
            scores.append(answers[q_id])
        
        for q_id in reversed:
            scores.append(6 - answers[q_id])
        
        return round(sum(scores) / len(scores), 2)

    @staticmethod
    def calculate_big_five_traits(answers: Dict[int, int]) -> Dict[str, float]:
        if len(answers) != 30:
            raise ValueError(f"Se esperan 30 respuestas, se recibieron {len(answers)}")
        
        return {
            trait_name: PersonalityService.calculate_trait_score(
                answers,
                questions['normal'],
                questions['reversed']
            )
            for trait_name, questions in TRAIT_MAPPING.items()
        }

    def get_personality_by_user_id(self, user_id: int) -> Personality | None:
        return self.db.query(Personality).filter(
            Personality.user_id == user_id
        ).first()

    def create_personality(self, user_id: int, traits: Dict[str, float]) -> Personality:
        personality = Personality(
            user_id=user_id,
            openness=traits['openness'],
            conscientiousness=traits['conscientiousness'],
            extraversion=traits['extraversion'],
            agreeableness=traits['agreeableness'],
            neuroticism=traits['neuroticism']
        )

        self.db.add(personality)
        return personality

    def update_personality(self, user_id: int, answers: Dict[int, int]) -> Dict[str, float]:
        personality = self.get_personality_by_user_id(user_id)
        if not personality:
            raise ValueError(f"No personality found for user {user_id}")

        traits = self.calculate_big_five_traits(answers)
        personality.openness = traits['openness']
        personality.conscientiousness = traits['conscientiousness']
        personality.extraversion = traits['extraversion']
        personality.agreeableness = traits['agreeableness']
        personality.neuroticism = traits['neuroticism']

        self.db.commit()
        self.db.refresh(personality)
        return traits