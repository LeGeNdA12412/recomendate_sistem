from typing import List, Optional
from pydantic import BaseModel, Field


class MovieResponse(BaseModel):
    id: int
    title: str
    release_year: Optional[int] = None
    genres: str
    director: Optional[str] = None
    cast: Optional[str] = None
    description: Optional[str] = None
    poster_url: Optional[str] = None
    avg_rating: Optional[float] = 0.0
    ratings_count: Optional[int] = 0
    weighted_score: Optional[float] = None
    similarity_score: Optional[float] = None
    predicted_rating: Optional[float] = None
    rank: Optional[int] = None
    method: Optional[str] = None
    explanation: Optional[str] = None

    class Config:
        from_attributes = True


class RatingCreate(BaseModel):
    user_id: int = Field(..., description="ID пользователя")
    movie_id: int = Field(..., description="ID фильма")
    rating: float = Field(..., ge=1.0, le=5.0, description="Оценка от 1.0 до 5.0")


class RatingResponse(BaseModel):
    id: int
    user_id: int
    movie_id: int
    movie_title: Optional[str] = None
    rating: float
    timestamp: Optional[str] = None

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=100)


class UserResponse(BaseModel):
    id: int
    username: str
    created_at: Optional[str] = None
    ratings_count: Optional[int] = 0

    class Config:
        from_attributes = True


class RecommendationResponse(BaseModel):
    status: str = "success"
    algorithm: str
    count: int
    target_user_id: Optional[int] = None
    target_movie_id: Optional[int] = None
    recommendations: List[MovieResponse]
