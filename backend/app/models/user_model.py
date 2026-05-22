from sqlalchemy import Integer, String, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id:            Mapped[int]        = mapped_column(Integer, primary_key=True, autoincrement=True)
    username:      Mapped[str]        = mapped_column(String(32), nullable=False, unique=True)
    gender:        Mapped[str | None] = mapped_column(String(16))
    age:           Mapped[int | None] = mapped_column(Integer)
    password_hash: Mapped[str]        = mapped_column(String(255), nullable=False)
    created_at:    Mapped[datetime]   = mapped_column(TIMESTAMP, server_default=func.now())

    # Relationships
    ratings:     Mapped[list["Rating"]]          = relationship("Rating",      back_populates="user")
    personality: Mapped["Personality | None"]    = relationship("Personality", back_populates="user", uselist=False)
    watchlist:   Mapped[list["Watchlist"]]       = relationship("Watchlist",   back_populates="user")

    def __repr__(self) -> str:
        return f"<User id={self.id} username='{self.username}'>"
