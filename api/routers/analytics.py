"""
FastAPI Router for Machine Learning Analytics and Diagnostics.
Powers Jupyter-style charts in Streamlit:
- Matrix Sparsity and Dataset Summary
- Rating and Genre Distributions
- Model Evaluation (RMSE, MAE, Precision@K, Recall@K)
- Scree Plot (SVD Explained Variance)
- PCA 2D Movie Embeddings
- Similarity Matrix Heatmaps
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.connection import get_db
from ml_engine.evaluation import MLEvaluationEngine

router = APIRouter(prefix="/analytics", tags=["ML Analytics & Diagnostics"])

eval_engine = MLEvaluationEngine()


@router.get("/summary", summary="Сводка по датасету и разреженность матрицы (Sparsity)")
def get_dataset_summary(db: Session = Depends(get_db)):
    return eval_engine.get_dataset_summary(db)


@router.get("/ratings-distribution", summary="Распределение оценок (Histogram / KDE)")
def get_ratings_distribution(db: Session = Depends(get_db)):
    return eval_engine.get_rating_distribution(db)


@router.get("/genres-distribution", summary="Распределение фильмов и средний балл по жанрам")
def get_genres_distribution(db: Session = Depends(get_db)):
    return eval_engine.get_genre_distribution(db)


@router.get("/model-metrics", summary="Метрики ML моделей: RMSE, MAE, Precision@K, Recall@K")
def get_model_metrics(db: Session = Depends(get_db)):
    return eval_engine.evaluate_models(db)


@router.get("/pca-projection", summary="2D PCA проекция эмбеддингов фильмов для кластеризации")
def get_pca_projection(db: Session = Depends(get_db)):
    return eval_engine.get_pca_movie_projection(db)


@router.get("/svd-scree", summary="Scree plot: сингулярные числа и объясненная дисперсия SVD")
def get_svd_scree(db: Session = Depends(get_db)):
    return eval_engine.get_svd_scree_data(db)


@router.get("/similarity-matrix", summary="Матрица попарного косинусного сходства для тепловой карты (Heatmap)")
def get_similarity_matrix(db: Session = Depends(get_db)):
    return eval_engine.get_similarity_heatmap_sample(db)
