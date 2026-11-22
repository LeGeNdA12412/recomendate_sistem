from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import recommender as r

app = FastAPI(title="Movie Recommender API")


class RatingRequest(BaseModel):
    user_id: int
    movie_id: int
    rating: float


@app.get("/")
def root():
    return {
        "status": "ok",
        "docs": "/docs",
        "help": "/api/help"
    }


@app.get("/api/popular")
def get_popular(count: int = Query(10, ge=1, le=30)):
    return r.get_top_popular(top_n=count)


@app.get("/api/collaborative/movie")
def get_collab_movie(title: str = Query(...), count: int = Query(10, ge=1, le=20)):
    recs = r.get_collaborative_by_movie(title, top_n=count)
    if not recs:
        raise HTTPException(status_code=404, detail="Фильм не найден")
    return recs


@app.get("/api/collaborative/user")
def get_collab_user(user_id: int = Query(...), count: int = Query(10, ge=1, le=20)):
    recs = r.get_collaborative_by_user(user_id, top_n=count)
    if not recs:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return recs


@app.get("/api/content-based")
def get_content_based(title: str = Query(...), count: int = Query(10, ge=1, le=20)):
    recs = r.get_content_based(title, top_n=count)
    if not recs:
        raise HTTPException(status_code=404, detail="Фильм не найден")
    return recs


@app.get("/api/personal")
def get_personal(user_id: int = Query(...), count: int = Query(10, ge=1, le=20)):
    return r.get_personal_recommendations(user_id, top_n=count)


@app.post("/api/rate")
def add_user_rating(req: RatingRequest):
    saved = r.rate_movie(req.user_id, req.movie_id, req.rating)
    if not saved:
        raise HTTPException(status_code=500, detail="Ошибка базы данных")
    return {"status": "ok"}


@app.get("/api/movies")
def list_movies():
    return r.get_all_movies()


@app.get("/api/users")
def list_users():
    return r.get_all_users()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
