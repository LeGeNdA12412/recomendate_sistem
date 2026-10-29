"""
FastAPI Router for Rating operations (submission, user ratings, user management).
All ratings are persisted directly into MySQL.
"""

from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Rating, Movie, User
from api.schemas import RatingCreate, RatingResponse, UserResponse, UserCreate

router = APIRouter(prefix="", tags=["Ratings & Users"])


@router.post(
    "/ratings",
    response_model=RatingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Оценить фильм (сохранение в БД MySQL)",
    description="Добавляет новую оценку или обновляет существующую оценку пользователя для данного фильма."
)
def create_or_update_rating(
    data: RatingCreate,
    db: Session = Depends(get_db)
):
    # Verify user exists
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"Пользователь с ID {data.user_id} не найден")

    # Verify movie exists
    movie = db.query(Movie).filter(Movie.id == data.movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail=f"Фильм с ID {data.movie_id} не найден")

    # Check if rating already exists (upsert)
    existing_rating = db.query(Rating).filter(
        Rating.user_id == data.user_id,
        Rating.movie_id == data.movie_id
    ).first()

    if existing_rating:
        existing_rating.rating = data.rating
        existing_rating.timestamp = datetime.utcnow()
        db.commit()
        db.refresh(existing_rating)
        rating_obj = existing_rating
    else:
        new_rating = Rating(
            user_id=data.user_id,
            movie_id=data.movie_id,
            rating=data.rating,
            timestamp=datetime.utcnow()
        )
        db.add(new_rating)
        db.commit()
        db.refresh(new_rating)
        rating_obj = new_rating

    return RatingResponse(
        id=rating_obj.id,
        user_id=rating_obj.user_id,
        movie_id=rating_obj.movie_id,
        movie_title=movie.title,
        rating=rating_obj.rating,
        timestamp=rating_obj.timestamp.isoformat() if rating_obj.timestamp else None
    )


@router.get(
    "/ratings/user/{user_id}",
    response_model=List[RatingResponse],
    summary="Получить все оценки конкретного пользователя"
)
def get_user_ratings(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"Пользователь с ID {user_id} не найден")

    ratings = db.query(Rating).filter(Rating.user_id == user_id).all()
    return [
        RatingResponse(
            id=r.id,
            user_id=r.user_id,
            movie_id=r.movie_id,
            movie_title=r.movie.title if r.movie else None,
            rating=r.rating,
            timestamp=r.timestamp.isoformat() if r.timestamp else None
        )
        for r in ratings
    ]


@router.get("/users", response_model=List[UserResponse], summary="Список всех пользователей")
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [UserResponse(**u.to_dict()) for u in users]


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Создать нового пользователя")
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == user_in.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Пользователь с таким именем уже существует")

    user = User(username=user_in.username)
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse(**user.to_dict())
