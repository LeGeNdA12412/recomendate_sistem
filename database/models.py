from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime,
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    ratings = relationship("Rating", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "ratings_count": len(self.ratings) if self.ratings else 0
        }


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    release_year = Column(Integer, nullable=True)
    genres = Column(String(255), nullable=False, index=True)
    director = Column(String(150), nullable=True)
    cast = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    poster_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    ratings = relationship("Rating", back_populates="movie", cascade="all, delete-orphan")

    def to_dict(self, include_stats: bool = False):
        data = {
            "id": self.id,
            "title": self.title,
            "release_year": self.release_year,
            "genres": self.genres,
            "director": self.director,
            "cast": self.cast,
            "description": self.description,
            "poster_url": self.poster_url,
        }
        if include_stats:
            try:
                values = [r.rating for r in (self.ratings or [])]
                if values:
                    data["avg_rating"] = round(sum(values) / len(values), 2)
                    data["ratings_count"] = len(values)
                else:
                    data["avg_rating"] = 0.0
                    data["ratings_count"] = 0
            except Exception:
                data["avg_rating"] = 0.0
                data["ratings_count"] = 0
        return data


class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, index=True)
    rating = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="ratings")
    movie = relationship("Movie", back_populates="ratings")

    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="uq_user_movie_rating"),
        Index("idx_user_movie", "user_id", "movie_id"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "movie_id": self.movie_id,
            "movie_title": self.movie.title if self.movie else None,
            "rating": self.rating,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
