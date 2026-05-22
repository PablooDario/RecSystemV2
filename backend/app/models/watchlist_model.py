from datetime import datetime

from sqlalchemy import Integer, TIMESTAMP, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.session import Base


class Watchlist(Base):
    __tablename__ = "watchlist"

    user_id:   Mapped[int]      = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    movie_id:  Mapped[int]      = mapped_column(Integer, ForeignKey("movies.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    added_at:  Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.now())

    user:  Mapped["User"]  = relationship("User", back_populates="watchlist")
    movie: Mapped["Movie"] = relationship("Movie", back_populates="watchlist")

    def __repr__(self) -> str:
        return f"<Watchlist user_id={self.user_id} movie_id={self.movie_id}>"
