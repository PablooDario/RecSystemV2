from sqlalchemy import Integer, String, Date, Text, JSON, DECIMAL, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


class Movie(Base):
    __tablename__ = "movies"

    id:            Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    tmdb_id:       Mapped[int | None]    = mapped_column(Integer, unique=True)
    title:         Mapped[str]           = mapped_column(String(128), nullable=False)
    genres:        Mapped[list | None]   = mapped_column(JSON)
    overview:      Mapped[str | None]    = mapped_column(Text)
    release_date:  Mapped[Date | None]   = mapped_column(Date)
    vote_average:  Mapped[float | None]  = mapped_column(DECIMAL(4, 2))
    vote_count:    Mapped[int | None]    = mapped_column(Integer)
    runtime:       Mapped[int | None]    = mapped_column(Integer)
    tagline:       Mapped[str | None]    = mapped_column(String(256))
    director:      Mapped[str | None]    = mapped_column(String(64))
    poster_path:   Mapped[str | None]    = mapped_column(String(64))
    backdrop_path: Mapped[str | None]    = mapped_column(String(64))
    score:         Mapped[float | None]  = mapped_column(Float)

    # Relationships
    ratings:       Mapped[list["Rating"]]       = relationship("Rating", back_populates="movie")
    actors:        Mapped[list["MovieActor"]]   = relationship("MovieActor", back_populates="movie")
    watchlist:     Mapped[list["Watchlist"]]    = relationship("Watchlist", back_populates="movie")

    def __repr__(self) -> str:
        return f"<Movie id={self.id} title='{self.title}'>"