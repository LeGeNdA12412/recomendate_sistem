"""
Unit tests for Movie Recommender System.
Verifies:
1. Popularity Bayesian Recommender
2. Collaborative Filtering (UBCF and IBCF)
3. Content-Based TF-IDF Recommender
4. Personal Hybrid Recommender (SVD + Content)
5. Rating creation and persistence
6. ML Evaluation engine
"""

import sys
import os
import unittest

# Ensure root directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.connection import SessionLocal, init_db
from database.seed_data import seed_database
from database.models import Movie, User, Rating
from ml_engine.popularity import PopularityRecommender
from ml_engine.collaborative import CollaborativeRecommender
from ml_engine.content_based import ContentBasedRecommender
from ml_engine.personal_hybrid import PersonalHybridRecommender
from ml_engine.evaluation import MLEvaluationEngine


class TestRecommenders(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()
        seed_database()
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_database_populated(self):
        movies_count = self.db.query(Movie).count()
        users_count = self.db.query(User).count()
        ratings_count = self.db.query(Rating).count()
        self.assertGreaterEqual(movies_count, 10, "Should have at least 10 movies")
        self.assertGreaterEqual(users_count, 5, "Should have at least 5 users")
        self.assertGreaterEqual(ratings_count, 20, "Should have at least 20 ratings")
        print(f"[OK] DB Populated: {movies_count} movies, {users_count} users, {ratings_count} ratings")

    def test_02_popularity_recommender(self):
        pop_rec = PopularityRecommender()
        top_10 = pop_rec.get_top_popular(self.db, limit=10)
        self.assertEqual(len(top_10), 10)
        self.assertIn("weighted_score", top_10[0])
        # Verify scores are sorted descending
        scores = [m["weighted_score"] for m in top_10]
        self.assertEqual(scores, sorted(scores, reverse=True))
        print(f"[OK] Popularity top movie: '{top_10[0]['title']}' (WR: {top_10[0]['weighted_score']})")

    def test_03_collaborative_user_based(self):
        cf_rec = CollaborativeRecommender()
        user = self.db.query(User).first()
        self.assertIsNotNone(user)
        recs = cf_rec.recommend_user_based(user_id=user.id, db=self.db, limit=5)
        self.assertGreater(len(recs), 0)
        self.assertIn("predicted_rating", recs[0])
        print(f"[OK] UBCF for '{user.username}': top rec '{recs[0]['title']}' (pred: {recs[0]['predicted_rating']})")

    def test_04_collaborative_item_based(self):
        cf_rec = CollaborativeRecommender()
        movie = self.db.query(Movie).filter(Movie.title == "Inception").first()
        if not movie:
            movie = self.db.query(Movie).first()
        recs = cf_rec.get_similar_items(movie_id=movie.id, db=self.db, limit=5)
        self.assertGreater(len(recs), 0)
        self.assertIn("similarity_score", recs[0])
        print(f"[OK] IBCF for '{movie.title}': top similar '{recs[0]['title']}' (sim: {recs[0]['similarity_score']})")

    def test_05_content_based_recommender(self):
        cb_rec = ContentBasedRecommender()
        movie = self.db.query(Movie).filter(Movie.title == "Inception").first()
        if not movie:
            movie = self.db.query(Movie).first()
        recs = cb_rec.get_similar_movies(movie_id=movie.id, db=self.db, limit=5)
        self.assertEqual(len(recs), 5)
        self.assertIn("similarity_score", recs[0])
        print(f"[OK] Content-Based for '{movie.title}': top similar '{recs[0]['title']}' (sim: {recs[0]['similarity_score']})")

    def test_06_personal_hybrid_recommender(self):
        hybrid_rec = PersonalHybridRecommender()
        user = self.db.query(User).first()
        recs = hybrid_rec.get_personal_recommendations(user_id=user.id, db=self.db, limit=5)
        self.assertEqual(len(recs), 5)
        self.assertIn("predicted_rating", recs[0])
        self.assertIn("explanation", recs[0])
        print(f"[OK] Hybrid for '{user.username}': '{recs[0]['title']}' ({recs[0]['explanation'][:60]}...)")

    def test_07_rating_creation_and_upsert(self):
        user = self.db.query(User).first()
        movie = self.db.query(Movie).first()

        # Insert or update
        r = self.db.query(Rating).filter(Rating.user_id == user.id, Rating.movie_id == movie.id).first()
        if not r:
            r = Rating(user_id=user.id, movie_id=movie.id, rating=4.5)
            self.db.add(r)
        else:
            r.rating = 5.0
        self.db.commit()

        re_read = self.db.query(Rating).filter(Rating.user_id == user.id, Rating.movie_id == movie.id).first()
        self.assertIsNotNone(re_read)
        self.assertIn(re_read.rating, [4.5, 5.0])
        print(f"[OK] Rating successfully written and verified in DB for user {user.id}")

    def test_08_ml_evaluation_metrics(self):
        eval_engine = MLEvaluationEngine()
        summary = eval_engine.get_dataset_summary(self.db)
        self.assertIn("sparsity_pct", summary)

        metrics = eval_engine.evaluate_models(self.db)
        self.assertIn("models", metrics)
        self.assertIn("SVD", metrics["models"])
        svd_m = metrics["models"]["SVD"]
        self.assertIn("rmse", svd_m)
        print(f"[OK] ML Evaluation completed. SVD RMSE: {svd_m['rmse']}, MAE: {svd_m['mae']}")


if __name__ == "__main__":
    unittest.main()
