import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from db import get_all_movies_df, get_all_ratings_df, save_rating


def load_data():
    movies = get_all_movies_df()
    ratings = get_all_ratings_df()
    return movies, ratings


def get_top_popular(top_n=10):
    movies, _ = load_data()
    if movies.empty:
        return []
    top = movies.sort_values(by=["rating", "votes"], ascending=False).head(top_n)
    return top.to_dict("records")


def get_collaborative_by_movie(title, top_n=10):
    movies, ratings = load_data()
    match = movies[movies["title"].str.lower() == title.lower()]
    if match.empty:
        return []

    target_id = match.iloc[0]["id"]
    pivot = ratings.pivot_table(index="user_id", columns="movie_id", values="rating").fillna(0)

    if target_id not in pivot.columns:
        return []

    sim_matrix = cosine_similarity(pivot.T)
    sim_df = pd.DataFrame(sim_matrix, index=pivot.columns, columns=pivot.columns)

    similar_ids = sim_df[target_id].sort_values(ascending=False).iloc[1:top_n + 1].index
    recs = movies[movies["id"].isin(similar_ids)].copy()
    return recs.to_dict("records")


def get_collaborative_by_user(user_id, top_n=10):
    movies, ratings = load_data()
    pivot = ratings.pivot_table(index="user_id", columns="movie_id", values="rating").fillna(0)

    if user_id not in pivot.index:
        return []

    user_sim = cosine_similarity(pivot)
    sim_df = pd.DataFrame(user_sim, index=pivot.index, columns=pivot.index)

    similar_users = sim_df[user_id].sort_values(ascending=False).iloc[1:4].index
    watched = ratings[ratings["user_id"] == user_id]["movie_id"].tolist()

    candidates = ratings[(ratings["user_id"].isin(similar_users)) & (~ratings["movie_id"].isin(watched))]
    if candidates.empty:
        return get_top_popular(top_n)

    top_ids = candidates.groupby("movie_id")["rating"].mean().sort_values(ascending=False).head(top_n).index
    recs = movies[movies["id"].isin(top_ids)].copy()
    return recs.to_dict("records")


def get_content_based(title, top_n=10):
    movies, _ = load_data()
    match = movies[movies["title"].str.lower() == title.lower()]
    if match.empty:
        return []

    target_idx = match.index[0]

    features = (
        movies["genres"] + " " + movies["genres"] + " " +
        movies["director"].fillna("") + " " + movies["cast"].fillna("") + " " +
        movies["description"].fillna("")
    )

    tfidf = TfidfVectorizer(token_pattern=r"(?u)\b[а-яА-ЯёЁ\w-]+\b")
    matrix = tfidf.fit_transform(features)
    sim = cosine_similarity(matrix[target_idx], matrix).flatten()

    sim_scores = list(enumerate(sim))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    top_indices = [i[0] for i in sim_scores[1:top_n + 1]]

    results = movies.iloc[top_indices].copy()
    results["similarity"] = [round(sim_scores[i + 1][1] * 100, 1) for i in range(len(top_indices))]
    return results.to_dict("records")


def get_personal_recommendations(user_id, top_n=10):
    movies, ratings = load_data()
    user_ratings = ratings[ratings["user_id"] == user_id]

    if user_ratings.empty:
        return get_top_popular(top_n)

    liked_ids = user_ratings[user_ratings["rating"] >= 4.0]["movie_id"].tolist()
    if not liked_ids:
        liked_ids = user_ratings.sort_values(by="rating", ascending=False)["movie_id"].head(3).tolist()

    watched_ids = user_ratings["movie_id"].tolist()

    features = (
        movies["genres"] + " " + movies["genres"] + " " +
        movies["director"].fillna("") + " " + movies["description"].fillna("")
    )
    tfidf = TfidfVectorizer(token_pattern=r"(?u)\b[а-яА-ЯёЁ\w-]+\b")
    matrix = tfidf.fit_transform(features)
    sim_matrix = cosine_similarity(matrix, matrix)

    scores = {}
    for mid in liked_ids:
        idx_match = movies[movies["id"] == mid].index
        if not idx_match.empty:
            idx = idx_match[0]
            for other_idx, s in enumerate(sim_matrix[idx]):
                other_id = movies.iloc[other_idx]["id"]
                if other_id not in watched_ids:
                    scores[other_id] = scores.get(other_id, 0) + s

    top_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:top_n]
    recs = movies[movies["id"].isin(top_ids)].copy()
    return recs.to_dict("records")


def rate_movie(user_id: int, movie_id: int, rating: float):
    return save_rating(user_id, movie_id, rating)


def get_all_movies():
    movies, _ = load_data()
    return movies.to_dict("records")


def get_all_users():
    _, ratings = load_data()
    if ratings.empty:
        return [1]
    return sorted(ratings["user_id"].unique().tolist())
