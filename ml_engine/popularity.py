from typing import List, Dict, Any, Optional
import pandas as pd
from sqlalchemy.orm import Session
from database.models import Movie, Rating


class PopularityRecommender:
    def __init__(self, min_ratings: int = 2):
        self.min_ratings = min_ratings

    def get_top_popular(
        self,
        db: Session,
        limit: int = 10,
        genre_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        movies = db.query(Movie).all()
        ratings = db.query(Rating).all()

        if not movies:
            return []

        if not ratings:
            res = []
            for m in movies[:limit]:
                data = m.to_dict()
                data["weighted_score"] = 0.0
                data["avg_rating"] = 0.0
                data["ratings_count"] = 0
                res.append(data)
            return res

        ratings_df = pd.DataFrame([
            {"movie_id": r.movie_id, "rating": float(r.rating)}
            for r in ratings
        ])

        stats = ratings_df.groupby("movie_id").agg(
            ratings_count=("rating", "count"),
            avg_rating=("rating", "mean")
        ).reset_index()

        C = float(ratings_df["rating"].mean())
        m = max(self.min_ratings, int(stats["ratings_count"].quantile(0.3) or 2))

        def weighted_rating(row):
            v = row["ratings_count"]
            R = row["avg_rating"]
            return (v / (v + m)) * R + (m / (v + m)) * C

        stats["weighted_score"] = stats.apply(weighted_rating, axis=1)

        stats_dict = {row["movie_id"]: row for _, row in stats.iterrows()}
        recommendations = []

        for movie in movies:
            if genre_filter and genre_filter.lower() not in movie.genres.lower():
                continue

            info = movie.to_dict()
            if movie.id in stats_dict:
                st = stats_dict[movie.id]
                info["ratings_count"] = int(st["ratings_count"])
                info["avg_rating"] = round(float(st["avg_rating"]), 2)
                info["weighted_score"] = round(float(st["weighted_score"]), 3)
            else:
                info["ratings_count"] = 0
                info["avg_rating"] = 0.0
                info["weighted_score"] = 0.0

            recommendations.append(info)

        recommendations.sort(
            key=lambda x: (x["weighted_score"], x["avg_rating"], x["ratings_count"]),
            reverse=True
        )

        top_list = recommendations[:limit]
        for idx, item in enumerate(top_list, start=1):
            item["rank"] = idx

        return top_list
