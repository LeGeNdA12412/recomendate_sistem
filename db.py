import os
import pymysql
import pandas as pd

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "1525",
    "database": "movie_recommender_db",
    "port": 3306,
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor
}


def get_connection():
    return pymysql.connect(**DB_CONFIG)


def get_all_movies_df():
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM movies")
            movies = pd.DataFrame(cur.fetchall())
            cur.execute("SELECT movie_id, AVG(rating) as avg_rating, COUNT(rating) as votes FROM ratings GROUP BY movie_id")
            stats = pd.DataFrame(cur.fetchall())
        conn.close()

        if not stats.empty and not movies.empty:
            movies = pd.merge(movies, stats, left_on="id", right_on="movie_id", how="left")
            movies["rating"] = movies["avg_rating"].round(1).fillna(4.0)
            movies["votes"] = movies["votes"].fillna(0).astype(int)
        else:
            movies["rating"] = 4.0
            movies["votes"] = 0

        return movies
    except Exception:
        if os.path.exists("movies.csv"):
            return pd.read_csv("movies.csv", encoding="utf-8")
        return pd.DataFrame()


def get_all_ratings_df():
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM ratings")
            ratings = pd.DataFrame(cur.fetchall())
        conn.close()
        return ratings
    except Exception:
        return pd.DataFrame(columns=["id", "user_id", "movie_id", "rating"])


def save_rating(user_id: int, movie_id: int, rating: float):
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO ratings (user_id, movie_id, rating) VALUES (%s, %s, %s)",
                (user_id, movie_id, rating)
            )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False
