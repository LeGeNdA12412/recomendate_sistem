from typing import List, Dict, Any
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session, joinedload
from database.models import Movie, Rating


class ContentBasedRecommender:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            token_pattern=r"(?u)\b[а-яА-ЯёЁ\w-]+\b",
            ngram_range=(1, 2),
            max_features=2500
        )
        self._tfidf_matrix = None
        self._movie_ids = []

    def _build_metadata_soup(self, movie: Movie) -> str:
        genres_clean = " ".join([g.strip().replace(" ", "-") for g in (movie.genres or "").split(",")])
        director_clean = (movie.director or "").replace(" ", "-")
        cast_clean = " ".join([(c.strip()).replace(" ", "-") for c in (movie.cast or "").split(",")[:4]])
        description_clean = movie.description or ""
        soup = f"{genres_clean} {genres_clean} {director_clean} {cast_clean} {description_clean}"
        return soup.lower()

    def fit(self, movies: List[Movie]):
        self._movie_ids = [m.id for m in movies]
        soups = [self._build_metadata_soup(m) for m in movies]
        self._tfidf_matrix = self.vectorizer.fit_transform(soups)

    def get_similar_movies(
        self,
        movie_id: int,
        db: Session,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        movies = db.query(Movie).options(joinedload(Movie.ratings)).all()
        if not movies:
            return []

        current_movie_dict = {m.id: m for m in movies}

        if self._tfidf_matrix is None or len(self._movie_ids) != len(movies):
            self.fit(movies)

        if movie_id not in current_movie_dict:
            return []

        target_idx = self._movie_ids.index(movie_id)
        target_vector = self._tfidf_matrix[target_idx]
        sim_scores = cosine_similarity(target_vector, self._tfidf_matrix).flatten()
        sorted_indices = np.argsort(sim_scores)[::-1]

        recommendations = []
        for idx in sorted_indices:
            cand_id = self._movie_ids[idx]
            if cand_id == movie_id:
                continue

            cand_movie = current_movie_dict.get(cand_id)
            if not cand_movie:
                continue

            score = float(sim_scores[idx])

            item = cand_movie.to_dict(include_stats=True)
            item["similarity_score"] = round(score, 3)
            item["method"] = "По контенту (TF-IDF)"
            recommendations.append(item)

            if len(recommendations) >= limit:
                break

        for rank, item in enumerate(recommendations, start=1):
            item["rank"] = rank

        return recommendations

    def recommend_for_user_profile(
        self,
        user_id: int,
        db: Session,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        movies = db.query(Movie).options(joinedload(Movie.ratings)).all()
        if not movies:
            return []

        current_movie_dict = {m.id: m for m in movies}

        if self._tfidf_matrix is None or len(self._movie_ids) != len(movies):
            self.fit(movies)

        user_ratings = db.query(Rating).filter(Rating.user_id == user_id).all()
        if not user_ratings:
            return []

        rated_movie_ids = {r.movie_id for r in user_ratings}
        high_ratings = [r for r in user_ratings if r.rating >= 3.5]
        weights_source = high_ratings if high_ratings else user_ratings

        user_profile_vector = np.zeros((1, self._tfidf_matrix.shape[1]))
        total_weight = 0.0

        for r in weights_source:
            if r.movie_id in current_movie_dict and r.movie_id in self._movie_ids:
                idx = self._movie_ids.index(r.movie_id)
                weight = float(r.rating)
                user_profile_vector += weight * self._tfidf_matrix[idx].toarray()
                total_weight += weight

        if total_weight > 0:
            user_profile_vector /= total_weight

        sim_scores = cosine_similarity(user_profile_vector, self._tfidf_matrix).flatten()
        sorted_indices = np.argsort(sim_scores)[::-1]

        recommendations = []
        for idx in sorted_indices:
            cand_id = self._movie_ids[idx]
            if cand_id in rated_movie_ids:
                continue

            cand_movie = current_movie_dict.get(cand_id)
            if not cand_movie:
                continue

            score = float(sim_scores[idx])

            item = cand_movie.to_dict(include_stats=True)
            item["similarity_score"] = round(score, 3)
            item["predicted_rating"] = round(min(5.0, 3.0 + score * 2.0), 2)
            item["method"] = "По профилю контента пользователя"
            recommendations.append(item)

            if len(recommendations) >= limit:
                break

        for rank, item in enumerate(recommendations, start=1):
            item["rank"] = rank

        return recommendations
