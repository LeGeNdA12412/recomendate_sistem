"""
FastAPI Router for Recommendation Endpoints.
Covers:
1. Popular movies (IMDb Bayesian rating)
2. Collaborative filtering (User-based & Item-based)
3. Content-based recommendations (TF-IDF & Cosine Similarity)
4. Personal recommendations (Hybrid SVD + Content)
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Movie, User
from api.schemas import RecommendationResponse, MovieResponse
from ml_engine.popularity import PopularityRecommender
from ml_engine.collaborative import CollaborativeRecommender
from ml_engine.content_based import ContentBasedRecommender
from ml_engine.personal_hybrid import PersonalHybridRecommender

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

popularity_rec = PopularityRecommender()
collaborative_rec = CollaborativeRecommender()
content_rec = ContentBasedRecommender()
hybrid_rec = PersonalHybridRecommender()


@router.get(
    "/popular",
    response_model=RecommendationResponse,
    summary="1. Top-10 популярных фильмов",
    description="Возвращает топ популярных фильмов на основе байесовской взвешенной формулы рейтинга IMDb (WR)."
)
def get_popular_movies(
    limit: int = Query(10, ge=1, le=50, description="Количество фильмов"),
    genre: Optional[str] = Query(None, description="Фильтр по жанру"),
    db: Session = Depends(get_db)
):
    results = popularity_rec.get_top_popular(db=db, limit=limit, genre_filter=genre)
    return RecommendationResponse(
        status="success",
        algorithm="Popularity Bayesian Weighted Rating (IMDb Formula)",
        count=len(results),
        recommendations=[MovieResponse(**r) for r in results]
    )


@router.get(
    "/collaborative/user-based",
    response_model=RecommendationResponse,
    summary="2a. Коллаборативная фильтрация (по пользователям)",
    description="Рекомендует фильмы целевому пользователю на основе сходства с другими пользователями (User-User Cosine Similarity)."
)
def get_user_based_recommendations(
    user_id: int = Query(..., description="ID пользователя для персонального прогноза"),
    limit: int = Query(10, ge=1, le=50, description="Количество рекомендаций"),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"Пользователь с ID {user_id} не найден")

    results = collaborative_rec.recommend_user_based(user_id=user_id, db=db, limit=limit)
    return RecommendationResponse(
        status="success",
        algorithm="User-Based Collaborative Filtering (UBCF)",
        count=len(results),
        target_user_id=user_id,
        recommendations=[MovieResponse(**r) for r in results]
    )


@router.get(
    "/collaborative/item-based",
    response_model=RecommendationResponse,
    summary="2b. Коллаборативная фильтрация (по фильмам)",
    description="Находит фильмы, наиболее похожие на указанный фильм по совместным оценкам пользователей (Item-Item Cosine Similarity)."
)
def get_item_based_recommendations(
    movie_id: int = Query(..., description="ID фильма для поиска похожих"),
    limit: int = Query(10, ge=1, le=50, description="Количество рекомендаций"),
    db: Session = Depends(get_db)
):
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail=f"Фильм с ID {movie_id} не найден")

    results = collaborative_rec.get_similar_items(movie_id=movie_id, db=db, limit=limit)
    return RecommendationResponse(
        status="success",
        algorithm="Item-Based Collaborative Filtering (Item-Item Sim)",
        count=len(results),
        target_movie_id=movie_id,
        recommendations=[MovieResponse(**r) for r in results]
    )


@router.get(
    "/collaborative/item-based-for-user",
    response_model=RecommendationResponse,
    summary="2c. Коллаборативная фильтрация по фильмам для пользователя",
    description="Прогнозирует рекомендации пользователю на основе сходства не просмотренных фильмов с теми, что он уже оценил."
)
def get_item_based_user_recommendations(
    user_id: int = Query(..., description="ID пользователя"),
    limit: int = Query(10, ge=1, le=50, description="Количество рекомендаций"),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"Пользователь с ID {user_id} не найден")

    results = collaborative_rec.recommend_item_based_for_user(user_id=user_id, db=db, limit=limit)
    return RecommendationResponse(
        status="success",
        algorithm="Item-Based Collaborative Filtering for User",
        count=len(results),
        target_user_id=user_id,
        recommendations=[MovieResponse(**r) for r in results]
    )


@router.get(
    "/content-based",
    response_model=RecommendationResponse,
    summary="3. Рекомендации по контенту (Content-Based)",
    description="Прогнозирует 10 рекомендованных фильмов на основе анализа контента (TF-IDF по жанрам, режиссеру, актерам и синопсису)."
)
def get_content_based_recommendations(
    movie_id: int = Query(..., description="ID фильма для поиска похожих по контенту"),
    limit: int = Query(10, ge=1, le=50, description="Количество рекомендаций"),
    db: Session = Depends(get_db)
):
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail=f"Фильм с ID {movie_id} не найден")

    results = content_rec.get_similar_movies(movie_id=movie_id, db=db, limit=limit)
    return RecommendationResponse(
        status="success",
        algorithm="Content-Based Filtering (TF-IDF & Cosine Similarity)",
        count=len(results),
        target_movie_id=movie_id,
        recommendations=[MovieResponse(**r) for r in results]
    )


@router.get(
    "/content-based/user-profile",
    response_model=RecommendationResponse,
    summary="3b. Рекомендации по контенту профиля пользователя",
    description="Рекомендует фильмы на основе TF-IDF профиля вкусов пользователя (агрегация понравившихся фильмов)."
)
def get_content_based_user_recommendations(
    user_id: int = Query(..., description="ID пользователя"),
    limit: int = Query(10, ge=1, le=50, description="Количество рекомендаций"),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"Пользователь с ID {user_id} не найден")

    results = content_rec.recommend_for_user_profile(user_id=user_id, db=db, limit=limit)
    return RecommendationResponse(
        status="success",
        algorithm="Content-Based User Profile Aggregation",
        count=len(results),
        target_user_id=user_id,
        recommendations=[MovieResponse(**r) for r in results]
    )

@router.get(
    "/personal",
    response_model=RecommendationResponse,
    summary="4. Персональные рекомендации для определенного пользователя",
    description="Формирует персональный список рекомендаций с помощью гибридного ансамбля: SVD факторизация матрицы рейтингов + Content-Based TF-IDF."
)
def get_personal_recommendations(
    user_id: int = Query(..., description="ID пользователя"),
    limit: int = Query(10, ge=1, le=50, description="Количество рекомендаций"),
    alpha: float = Query(0.65, ge=0.0, le=1.0, description="Вес коллаборативной части SVD (1 - alpha — вес контента)"),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"Пользователь с ID {user_id} не найден")

    results = hybrid_rec.get_personal_recommendations(
        user_id=user_id,
        db=db,
        limit=limit,
        alpha_override=alpha
    )
    return RecommendationResponse(
        status="success",
        algorithm="Hybrid Personal Recommender (SVD Matrix Factorization + Content TF-IDF)",
        count=len(results),
        target_user_id=user_id,
        recommendations=[MovieResponse(**r) for r in results]
    )
