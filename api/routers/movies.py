"""
FastAPI Router for Movie operations (browsing, searching, details).
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from database.connection import get_db
from database.models import Movie
from api.schemas import MovieResponse

router = APIRouter(prefix="/movies", tags=["Movies"])


@router.get("", response_model=List[MovieResponse], summary="Получить список фильмов с фильтрацией")
def list_movies(
    query: Optional[str] = Query(None, description="Поиск по названию или описанию"),
    genre: Optional[str] = Query(None, description="Фильтр по жанру"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    q = db.query(Movie).options(joinedload(Movie.ratings))
    if query:
        pattern = f"%{query}%"
        q = q.filter(or_(Movie.title.ilike(pattern), Movie.description.ilike(pattern)))
    if genre:
        q = q.filter(Movie.genres.ilike(f"%{genre}%"))

    movies = q.offset(skip).limit(limit).all()
    return [MovieResponse(**m.to_dict(include_stats=True)) for m in movies]


@router.get("/genres", response_model=List[str], summary="Список всех доступных жанров")
def get_genres(db: Session = Depends(get_db)):
    movies = db.query(Movie.genres).all()
    unique_genres = set()
    for row in movies:
        if row[0]:
            for g in row[0].split(","):
                unique_genres.add(g.strip())
    return sorted(list(unique_genres))


@router.get("/{movie_id}", response_model=MovieResponse, summary="Получить информацию о конкретном фильме")
def get_movie_detail(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(Movie).options(joinedload(Movie.ratings)).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Фильм не найден")
    return MovieResponse(**movie.to_dict(include_stats=True))
