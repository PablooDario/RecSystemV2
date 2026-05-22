from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

class MovieActor(Base):
    __tablename__ = "movie_actors"

    movie_id: Mapped[int] = mapped_column(Integer, ForeignKey("movies.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    actor_id: Mapped[int] = mapped_column(Integer, ForeignKey("actors.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)

    # Relationships
    movie:         Mapped["Movie"]       = relationship("Movie", back_populates="actors")
    actor:         Mapped["Actor"]       = relationship("Actor", back_populates="movies")

    def __repr__(self) -> str:
        return f"<MovieActor movie_id={self.movie_id} actor_id={self.actor_id}>"