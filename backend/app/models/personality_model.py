from sqlalchemy import Integer, DECIMAL, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


class Personality(Base):
    __tablename__ = "personalities"

    # PK is also FK to users.id (one-to-one relationship)
    user_id:          Mapped[int]   = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    openness:         Mapped[float] = mapped_column(DECIMAL(3, 2), nullable=False)
    conscientiousness:Mapped[float] = mapped_column(DECIMAL(3, 2), nullable=False)
    extraversion:     Mapped[float] = mapped_column(DECIMAL(3, 2), nullable=False)
    agreeableness:    Mapped[float] = mapped_column(DECIMAL(3, 2), nullable=False)
    neuroticism:      Mapped[float] = mapped_column(DECIMAL(3, 2), nullable=False)

    # Inverse relationship to User
    user: Mapped["User"] = relationship("User", back_populates="personality")

    def __repr__(self) -> str:
        return f"<Personality user_id={self.user_id}>"