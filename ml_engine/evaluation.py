from typing import Dict, Any, List
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
from database.models import Movie, Rating, User
from ml_engine.content_based import ContentBasedRecommender


class MLEvaluationEngine:
    def __init__(self):
        self.content_rec = ContentBasedRecommender()

    def get_dataset_summary(self, db: Session) -> Dict[str, Any]:
        total_users = db.query(User).count()
        total_movies = db.query(Movie).count()
        ratings = db.query(Rating).all()
        total_ratings = len(ratings)

        if total_users == 0 or total_movies == 0:
            return {
                "total_users": 0,
                "total_movies": 0,
                "total_ratings": 0,
                "sparsity_pct": 100.0,
                "mean_rating": 0.0,
                "std_rating": 0.0,
            }

        total_possible = total_users * total_movies
        sparsity = (1.0 - (total_ratings / total_possible)) * 100.0 if total_possible > 0 else 100.0

        scores = [float(r.rating) for r in ratings]
        mean_score = float(np.mean(scores)) if scores else 0.0
        std_score = float(np.std(scores)) if scores else 0.0

        return {
            "total_users": total_users,
            "total_movies": total_movies,
            "total_ratings": total_ratings,
            "matrix_dimensions": f"{total_users} users x {total_movies} movies",
            "possible_ratings": total_possible,
            "sparsity_pct": round(sparsity, 2),
            "density_pct": round(100.0 - sparsity, 2),
            "mean_rating": round(mean_score, 2),
            "std_rating": round(std_score, 2),
        }

    def get_rating_distribution(self, db: Session) -> List[Dict[str, Any]]:
        ratings = db.query(Rating).all()
        if not ratings:
            return []

        scores = [float(r.rating) for r in ratings]
        counts = pd.Series(scores).value_counts().sort_index()

        return [
            {"rating": float(k), "count": int(v)}
            for k, v in counts.items()
        ]

    def get_genre_distribution(self, db: Session) -> List[Dict[str, Any]]:
        movies = db.query(Movie).all()
        ratings = db.query(Rating).all()

        movie_ratings = {}
        for r in ratings:
            movie_ratings.setdefault(r.movie_id, []).append(float(r.rating))

        genre_counts = {}
        genre_scores = {}

        for m in movies:
            avg_m = np.mean(movie_ratings[m.id]) if m.id in movie_ratings else None
            genres = [g.strip() for g in (m.genres or "").split(",") if g.strip()]
            for g in genres:
                genre_counts[g] = genre_counts.get(g, 0) + 1
                if avg_m is not None:
                    genre_scores.setdefault(g, []).append(avg_m)

        res = []
        for g, count in sorted(genre_counts.items(), key=lambda x: x[1], reverse=True):
            avg_score = round(float(np.mean(genre_scores[g])), 2) if g in genre_scores else 0.0
            res.append({
                "genre": g,
                "count": count,
                "avg_rating": avg_score
            })
        return res

    def evaluate_models(self, db: Session, test_ratio: float = 0.2) -> Dict[str, Any]:
        ratings = db.query(Rating).all()
        if len(ratings) < 15:
            return {"error": "Недостаточно данных для оценки"}

        df = pd.DataFrame([
            {"user_id": r.user_id, "movie_id": r.movie_id, "rating": float(r.rating)}
            for r in ratings
        ])

        test_df = df.sample(frac=test_ratio, random_state=42)
        train_df = df.drop(test_df.index)

        train_matrix = train_df.pivot_table(index="user_id", columns="movie_id", values="rating")
        global_mean = float(train_df["rating"].mean())
        user_means = train_matrix.mean(axis=1)

        baseline_preds = []
        for _, row in test_df.iterrows():
            u, m = row["user_id"], row["movie_id"]
            pred = user_means.get(u, global_mean)
            baseline_preds.append(pred)

        matrix_centered = train_matrix.sub(user_means, axis=0).fillna(0)
        n_comp = min(5, len(train_matrix) - 1, len(train_matrix.columns) - 1)
        n_comp = max(2, n_comp)

        svd = TruncatedSVD(n_components=n_comp, random_state=42)
        u_factors = svd.fit_transform(matrix_centered)
        i_factors = svd.components_
        svd_recon = pd.DataFrame(
            np.dot(u_factors, i_factors),
            index=train_matrix.index,
            columns=train_matrix.columns
        )

        svd_preds = []
        for _, row in test_df.iterrows():
            u, m = row["user_id"], row["movie_id"]
            u_mean = user_means.get(u, global_mean)
            if u in svd_recon.index and m in svd_recon.columns:
                pred = u_mean + svd_recon.loc[u, m]
                pred = np.clip(pred, 1.0, 5.0)
            else:
                pred = u_mean
            svd_preds.append(float(pred))

        user_sim_df = pd.DataFrame(
            cosine_similarity(matrix_centered.values),
            index=matrix_centered.index,
            columns=matrix_centered.index
        )
        ubcf_preds = []
        for _, row in test_df.iterrows():
            u, m = row["user_id"], row["movie_id"]
            u_mean = user_means.get(u, global_mean)
            if u in user_sim_df.index and m in train_matrix.columns:
                users_rated = train_matrix[m].dropna()
                common = users_rated.index.intersection(user_sim_df.columns).drop(u, errors="ignore")
                if not common.empty:
                    sims = user_sim_df.loc[u, common]
                    pos = sims[sims > 0]
                    if not pos.empty:
                        diffs = train_matrix.loc[pos.index, m] - user_means.loc[pos.index]
                        pred = u_mean + (pos * diffs).sum() / pos.sum()
                        ubcf_preds.append(float(np.clip(pred, 1.0, 5.0)))
                        continue
            ubcf_preds.append(u_mean)

        item_matrix = matrix_centered.T
        item_sim_df = pd.DataFrame(
            cosine_similarity(item_matrix.values),
            index=item_matrix.index,
            columns=item_matrix.index
        )
        ibcf_preds = []
        for _, row in test_df.iterrows():
            u, m = row["user_id"], row["movie_id"]
            u_mean = user_means.get(u, global_mean)
            if u in train_matrix.index and m in item_sim_df.index:
                rated_by_u = train_matrix.loc[u].dropna()
                common_items = rated_by_u.index.intersection(item_sim_df.columns).drop(m, errors="ignore")
                if not common_items.empty:
                    sims = item_sim_df.loc[m, common_items]
                    pos = sims[sims > 0]
                    if not pos.empty:
                        pred = (pos * rated_by_u.loc[pos.index]).sum() / pos.sum()
                        ibcf_preds.append(float(np.clip(pred, 1.0, 5.0)))
                        continue
            ibcf_preds.append(u_mean)

        y_true = test_df["rating"].values

        def calc_metrics(y_p):
            rmse = float(np.sqrt(mean_squared_error(y_true, y_p)))
            mae = float(mean_absolute_error(y_true, y_p))
            true_rel = (y_true >= 4.0)
            pred_rel = (np.array(y_p) >= 3.8)
            tp = np.sum(true_rel & pred_rel)
            prec = float(tp / np.sum(pred_rel)) if np.sum(pred_rel) > 0 else 0.0
            rec = float(tp / np.sum(true_rel)) if np.sum(true_rel) > 0 else 0.0
            return {
                "rmse": round(rmse, 3),
                "mae": round(mae, 3),
                "precision": round(prec, 3),
                "recall": round(rec, 3)
            }

        return {
            "test_samples_count": len(test_df),
            "train_samples_count": len(train_df),
            "models": {
                "Базовая модель": calc_metrics(baseline_preds),
                "User-Based": calc_metrics(ubcf_preds),
                "Item-Based": calc_metrics(ibcf_preds),
                "SVD": calc_metrics(svd_preds),
            }
        }

    def get_pca_movie_projection(self, db: Session) -> List[Dict[str, Any]]:
        movies = db.query(Movie).all()
        if len(movies) < 3:
            return []

        self.content_rec.fit(movies)
        tfidf_mat = self.content_rec._tfidf_matrix.toarray()

        pca = PCA(n_components=2, random_state=42)
        coords = pca.fit_transform(tfidf_mat)

        ratings = db.query(Rating).all()
        m_ratings = {}
        for r in ratings:
            m_ratings.setdefault(r.movie_id, []).append(float(r.rating))

        results = []
        for i, m in enumerate(movies):
            avg_r = round(float(np.mean(m_ratings[m.id])), 2) if m.id in m_ratings else 0.0
            primary_genre = m.genres.split(",")[0].strip() if m.genres else "Другое"
            results.append({
                "movie_id": m.id,
                "title": m.title,
                "pc1": round(float(coords[i, 0]), 4),
                "pc2": round(float(coords[i, 1]), 4),
                "genre": primary_genre,
                "release_year": m.release_year,
                "avg_rating": avg_r
            })

        return results

    def get_svd_scree_data(self, db: Session) -> Dict[str, Any]:
        ratings = db.query(Rating).all()
        if not ratings:
            return {"components": [], "explained_variance": [], "cumulative_variance": []}

        df = pd.DataFrame([
            {"user_id": r.user_id, "movie_id": r.movie_id, "rating": float(r.rating)}
            for r in ratings
        ])
        matrix = df.pivot_table(index="user_id", columns="movie_id", values="rating").fillna(0)

        max_k = min(8, min(matrix.shape) - 1)
        if max_k < 2:
            return {"components": [], "explained_variance": [], "cumulative_variance": []}

        svd = TruncatedSVD(n_components=max_k, random_state=42)
        svd.fit(matrix)

        exp_var = [round(float(v) * 100, 2) for v in svd.explained_variance_ratio_]
        cum_var = [round(float(v) * 100, 2) for v in np.cumsum(svd.explained_variance_ratio_)]

        return {
            "components": [f"Фактор {i+1}" for i in range(max_k)],
            "singular_values": [round(float(s), 2) for s in svd.singular_values_],
            "explained_variance_pct": exp_var,
            "cumulative_variance_pct": cum_var
        }

    def get_similarity_heatmap_sample(self, db: Session, limit: int = 8) -> Dict[str, Any]:
        from ml_engine.popularity import PopularityRecommender
        top_movies = PopularityRecommender().get_top_popular(db, limit=limit)
        movie_ids = [m["id"] for m in top_movies]
        titles = [m["title"] for m in top_movies]

        all_movies = db.query(Movie).all()
        self.content_rec.fit(all_movies)

        indices = [self.content_rec._movie_ids.index(mid) for mid in movie_ids if mid in self.content_rec._movie_ids]
        sub_matrix = self.content_rec._tfidf_matrix[indices]
        sim_mat = cosine_similarity(sub_matrix)

        matrix_values = [[round(float(val), 2) for val in row] for row in sim_mat]
        return {
            "titles": titles,
            "matrix": matrix_values
        }
