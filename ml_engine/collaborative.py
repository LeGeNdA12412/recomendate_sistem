from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session, joinedload
from database.models import Movie, Rating


class CollaborativeRecommender:
    def __init__(self, k_neighbors: int = 10, min_common_ratings: int = 1):
        self.k_neighbors = k_neighbors
        self.min_common_ratings = min_common_ratings

    def _get_rating_matrix(self, db: Session) -> Tuple[pd.DataFrame, Dict[int, Movie]]:
        movies = db.query(Movie).options(joinedload(Movie.ratings)).all()
        ratings = db.query(Rating).all()
        movie_dict = {m.id: m for m in movies}

        if not ratings:
            return pd.DataFrame(), movie_dict

        data = [
            {"user_id": r.user_id, "movie_id": r.movie_id, "rating": float(r.rating)}
            for r in ratings
        ]
        df = pd.DataFrame(data)
        rating_matrix = df.pivot_table(
            index="user_id",
            columns="movie_id",
            values="rating"
        )
        return rating_matrix, movie_dict

    def recommend_user_based(
        self,
        user_id: int,
        db: Session,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        rating_matrix, movie_dict = self._get_rating_matrix(db)

        if rating_matrix.empty or user_id not in rating_matrix.index:
            return []

        target_user_ratings = rating_matrix.loc[user_id]
        rated_movie_ids = set(target_user_ratings.dropna().index)
        candidate_movie_ids = [m_id for m_id in rating_matrix.columns if m_id not in rated_movie_ids]

        if not candidate_movie_ids:
            return []

        user_means = rating_matrix.mean(axis=1)
        matrix_centered = rating_matrix.sub(user_means, axis=0).fillna(0)

        target_vector = matrix_centered.loc[[user_id]].values
        all_vectors = matrix_centered.values
        sim_scores = cosine_similarity(target_vector, all_vectors)[0]

        user_ids = rating_matrix.index.tolist()
        sim_series = pd.Series(sim_scores, index=user_ids).drop(index=user_id, errors="ignore")
        target_mean = user_means.loc[user_id]

        predicted_ratings = {}
        for m_id in candidate_movie_ids:
            movie_ratings = rating_matrix[m_id].dropna()
            if movie_ratings.empty:
                continue

            common_users = movie_ratings.index.intersection(sim_series.index)
            if len(common_users) < self.min_common_ratings:
                continue

            user_sims = sim_series.loc[common_users]
            top_neighbors = user_sims.sort_values(ascending=False).head(self.k_neighbors)
            pos_neighbors = top_neighbors[top_neighbors > 0]
            if pos_neighbors.empty:
                continue

            sim_sum = pos_neighbors.sum()
            diffs = rating_matrix.loc[pos_neighbors.index, m_id] - user_means.loc[pos_neighbors.index]
            weighted_diff = (pos_neighbors * diffs).sum()

            pred = target_mean + (weighted_diff / sim_sum)
            predicted_ratings[m_id] = float(np.clip(pred, 1.0, 5.0))

        if not predicted_ratings:
            return []

        sorted_candidates = sorted(predicted_ratings.items(), key=lambda x: x[1], reverse=True)[:limit]

        results = []
        for rank, (m_id, score) in enumerate(sorted_candidates, start=1):
            movie = movie_dict.get(m_id)
            if not movie:
                continue
            item = movie.to_dict(include_stats=True)
            item["predicted_rating"] = round(score, 2)
            item["rank"] = rank
            item["method"] = "Коллаборативная по пользователям"
            results.append(item)

        return results

    def get_similar_items(
        self,
        movie_id: int,
        db: Session,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        rating_matrix, movie_dict = self._get_rating_matrix(db)

        if rating_matrix.empty or movie_id not in rating_matrix.columns:
            return []

        user_means = rating_matrix.mean(axis=1)
        matrix_centered = rating_matrix.sub(user_means, axis=0).fillna(0)
        item_matrix = matrix_centered.T

        target_vector = item_matrix.loc[[movie_id]].values
        all_vectors = item_matrix.values
        sim_scores = cosine_similarity(target_vector, all_vectors)[0]

        movie_ids = item_matrix.index.tolist()
        sim_series = pd.Series(sim_scores, index=movie_ids).drop(index=movie_id, errors="ignore")
        top_similar = sim_series.sort_values(ascending=False).head(limit)

        results = []
        for rank, (m_id, score) in enumerate(top_similar.items(), start=1):
            movie = movie_dict.get(m_id)
            if not movie:
                continue
            item = movie.to_dict(include_stats=True)
            item["similarity_score"] = round(float(score), 3)
            item["rank"] = rank
            item["method"] = "Коллаборативная по фильмам"
            results.append(item)

        return results

    def recommend_item_based_for_user(
        self,
        user_id: int,
        db: Session,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        rating_matrix, movie_dict = self._get_rating_matrix(db)

        if rating_matrix.empty or user_id not in rating_matrix.index:
            return []

        user_ratings = rating_matrix.loc[user_id].dropna()
        if user_ratings.empty:
            return []

        rated_movie_ids = set(user_ratings.index)
        candidate_movie_ids = [m_id for m_id in rating_matrix.columns if m_id not in rated_movie_ids]

        if not candidate_movie_ids:
            return []

        user_means = rating_matrix.mean(axis=1)
        matrix_centered = rating_matrix.sub(user_means, axis=0).fillna(0)
        item_matrix = matrix_centered.T

        item_sim_df = pd.DataFrame(
            cosine_similarity(item_matrix.values),
            index=item_matrix.index,
            columns=item_matrix.index
        )

        predicted_ratings = {}
        for cand_id in candidate_movie_ids:
            if cand_id not in item_sim_df.index:
                continue

            sims = item_sim_df.loc[cand_id, list(rated_movie_ids)]
            pos_sims = sims[sims > 0]
            if pos_sims.empty:
                continue

            ratings_for_sim = user_ratings.loc[pos_sims.index]
            pred = (pos_sims * ratings_for_sim).sum() / pos_sims.sum()
            predicted_ratings[cand_id] = float(np.clip(pred, 1.0, 5.0))

        if not predicted_ratings:
            return []

        sorted_candidates = sorted(predicted_ratings.items(), key=lambda x: x[1], reverse=True)[:limit]

        results = []
        for rank, (m_id, score) in enumerate(sorted_candidates, start=1):
            movie = movie_dict.get(m_id)
            if not movie:
                continue
            item = movie.to_dict(include_stats=True)
            item["predicted_rating"] = round(score, 2)
            item["rank"] = rank
            item["method"] = "Коллаборативная по фильмам для пользователя"
            results.append(item)

        return results
