import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.connection import init_db, DB_DIALECT, DB_NAME
from database.seed_data import seed_database
from api.routers import recommendations, movies, ratings, analytics


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_database()
    yield


app = FastAPI(
    title="Movie Recommendation System API",
    description="REST API для рекомендательной системы фильмов",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recommendations.router, prefix="/api")
app.include_router(movies.router, prefix="/api")
app.include_router(ratings.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")

static_dir = os.path.join(os.path.dirname(__file__), "..", "app", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", summary="Статус API")
def root():
    return {
        "status": "online",
        "service": "Movie Recommendation System API",
        "version": "1.0.0",
        "database": DB_DIALECT,
        "database_name": DB_NAME,
        "docs_url": "/docs"
    }
