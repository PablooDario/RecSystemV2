from sqlalchemy import Integer, TIMESTAMP, DECIMAL, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from app.db.session import Base


class Rating(Base):
    __tablename__ = "ratings"

    # Compound PK: user_id + movie_id
    user_id:   Mapped[int]      = mapped_column(Integer, ForeignKey("users.id",  ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    movie_id:  Mapped[int]      = mapped_column(Integer, ForeignKey("movies.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    rating:    Mapped[float]    = mapped_column(DECIMAL(2, 1), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())

    # Relationships
    user:  Mapped["User"]  = relationship("User",  back_populates="ratings")
    movie: Mapped["Movie"] = relationship("Movie", back_populates="ratings")

    def __repr__(self) -> str:
        return f"<Rating user_id={self.user_id} movie_id={self.movie_id} rating={self.rating}>"
