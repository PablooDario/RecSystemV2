from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

class Actor(Base):
    __tablename__ = "actors"

    id:            Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    tmdb_id:       Mapped[int | None]    = mapped_column(Integer, unique=True)
    name:          Mapped[str]           = mapped_column(String(64), nullable=False)
    profile_path:  Mapped[str | None]    = mapped_column(String(64))

    # Relationships
    movies:        Mapped[list["MovieActor"]] = relationship("MovieActor", back_populates="actor")

    def __repr__(self) -> str:
        return f"<Actor id={self.id} name='{self.name}'>"
