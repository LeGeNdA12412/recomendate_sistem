from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from sklearn.decomposition import TruncatedSVD
from sqlalchemy.orm import Session, joinedload
from database.models import Movie, Rating, User
from ml_engine.content_based import ContentBasedRecommender


class PersonalHybridRecommender:
    def __init__(self, n_components: int = 5, alpha: float = 0.65):
        self.n_components = n_components
        self.alpha = alpha
        self.content_rec = ContentBasedRecommender()

    def get_personal_recommendations(
        self,
        user_id: int,
        db: Session,
        limit: int = 10,
        alpha_override: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        alpha = alpha_override if alpha_override is not None else self.alpha

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return []

        movies = db.query(Movie).options(joinedload(Movie.ratings)).all()
        ratings = db.query(Rating).all()
        if not movies:
            return []

        movie_dict = {m.id: m for m in movies}
        user_ratings = db.query(Rating).filter(Rating.user_id == user_id).all()
        rated_movie_ids = {r.movie_id for r in user_ratings}

        candidate_ids = [m.id for m in movies if m.id not in rated_movie_ids]
        if not candidate_ids:
            return []

        ratings_data = [
            {"user_id": r.user_id, "movie_id": r.movie_id, "rating": float(r.rating)}
            for r in ratings
        ]
        df_ratings = pd.DataFrame(ratings_data)
        matrix = df_ratings.pivot_table(index="user_id", columns="movie_id", values="rating")

        global_mean = float(df_ratings["rating"].mean())
        user_means = matrix.mean(axis=1)

        cf_scores = {}
        if len(matrix) >= 2 and len(matrix.columns) >= 2:
            try:
                matrix_centered = matrix.sub(user_means, axis=0).fillna(0)
                k = min(self.n_components, len(matrix) - 1, len(matrix.columns) - 1)
                k = max(2, k)

                svd = TruncatedSVD(n_components=k, random_state=42)
                user_factors = svd.fit_transform(matrix_centered)
                item_factors = svd.components_

                reconstructed = np.dot(user_factors, item_factors)
                recon_df = pd.DataFrame(reconstructed, index=matrix.index, columns=matrix.columns)
                target_user_mean = user_means.get(user_id, global_mean)

                if user_id in recon_df.index:
                    for cid in candidate_ids:
                        if cid in recon_df.columns:
                            pred = target_user_mean + recon_df.loc[user_id, cid]
                            cf_scores[cid] = float(np.clip(pred, 1.0, 5.0))
            except Exception:
                pass

        for cid in candidate_ids:
            if cid not in cf_scores:
                movie_ratings = df_ratings[df_ratings["movie_id"] == cid]
                cf_scores[cid] = float(movie_ratings["rating"].mean()) if not movie_ratings.empty else global_mean

        content_items = self.content_rec.recommend_for_user_profile(user_id=user_id, db=db, limit=len(candidate_ids))
        content_scores = {}
        for item in content_items:
            sim = item.get("similarity_score", 0.0)
            content_scores[item["id"]] = 1.0 + sim * 4.0

        for cid in candidate_ids:
            if cid not in content_scores:
                content_scores[cid] = global_mean

        hybrid_results = []
        for cid in candidate_ids:
            cf_val = cf_scores[cid]
            cnt_val = content_scores[cid]
            final_pred = alpha * cf_val + (1.0 - alpha) * cnt_val

            movie = movie_dict.get(cid)
            if not movie:
                continue

            info = movie.to_dict(include_stats=True)
            info["predicted_rating"] = round(float(final_pred), 2)
            info["cf_component"] = round(float(cf_val), 2)
            info["content_component"] = round(float(cnt_val), 2)
            info["method"] = "Персональные рекомендации"
            genres_list = [g.strip() for g in movie.genres.split(",")]
            info["explanation"] = f"Подходит по оценкам и жанрам: {', '.join(genres_list[:2])}"
            hybrid_results.append(info)

        hybrid_results.sort(key=lambda x: x["predicted_rating"], reverse=True)
        top_recommendations = hybrid_results[:limit]

        for rank, item in enumerate(top_recommendations, start=1):
            item["rank"] = rank

        return top_recommendations
