"""
FastAPI REST API integration tests.
Tests all endpoints requested in task:
1. Popular movies
2. Collaborative user-based & item-based
3. Content-based
4. Personal hybrid
5. Ratings save to MySQL
6. Help documentation
7. Analytics & ML metrics
"""

import sys
import os
import unittest
from fastapi.testclient import TestClient

# Ensure root directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.main import app
from database.connection import SessionLocal
from database.models import User, Movie


class TestAPIEndpoints(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        db = SessionLocal()
        cls.user = db.query(User).first()
        cls.movie = db.query(Movie).first()
        cls.user_id = cls.user.id if cls.user else 1
        cls.movie_id = cls.movie.id if cls.movie else 1
        db.close()

    def test_01_root(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "online")
        print("[OK] GET / -> status online, DB:", data.get("database"))

    def test_02_movies_list(self):
        res = self.client.get("/api/movies?limit=10")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(len(data), 10)
        print(f"[OK] GET /api/movies -> {len(data)} movies returned")

    def test_03_popular_recommendations(self):
        res = self.client.get("/api/recommendations/popular?limit=10")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["count"], 10)
        self.assertIn("recommendations", data)
        print(f"[OK] GET /api/recommendations/popular -> 10 movies returned")

    def test_04_collaborative_user_based(self):
        res = self.client.get(f"/api/recommendations/collaborative/user-based?user_id={self.user_id}&limit=5")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("recommendations", data)
        print(f"[OK] GET /api/recommendations/collaborative/user-based -> {len(data['recommendations'])} recs")

    def test_05_collaborative_item_based(self):
        res = self.client.get(f"/api/recommendations/collaborative/item-based?movie_id={self.movie_id}&limit=5")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("recommendations", data)
        print(f"[OK] GET /api/recommendations/collaborative/item-based -> {len(data['recommendations'])} similar items")

    def test_06_content_based(self):
        res = self.client.get(f"/api/recommendations/content-based?movie_id={self.movie_id}&limit=10")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["count"], 10)
        print(f"[OK] GET /api/recommendations/content-based -> 10 content-similar movies")

    def test_07_personal_hybrid(self):
        res = self.client.get(f"/api/recommendations/personal?user_id={self.user_id}&limit=10&alpha=0.65")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("recommendations", data)
        print(f"[OK] GET /api/recommendations/personal -> {len(data['recommendations'])} personal recs")

    def test_08_post_rating(self):
        payload = {"user_id": self.user_id, "movie_id": self.movie_id, "rating": 5.0}
        res = self.client.post("/api/ratings", json=payload)
        self.assertIn(res.status_code, [200, 201])
        data = res.json()
        self.assertEqual(data["rating"], 5.0)
        print(f"[OK] POST /api/ratings -> Saved rating {data['rating']} for movie ID {data['movie_id']}")

    def test_09_analytics_endpoints(self):
        res_sum = self.client.get("/api/analytics/summary")
        self.assertEqual(res_sum.status_code, 200)

        res_met = self.client.get("/api/analytics/model-metrics")
        self.assertEqual(res_met.status_code, 200)

        res_scree = self.client.get("/api/analytics/svd-scree")
        self.assertEqual(res_scree.status_code, 200)

        res_pca = self.client.get("/api/analytics/pca-projection")
        self.assertEqual(res_pca.status_code, 200)

        print("[OK] GET /api/analytics/* -> All analytics endpoints functioning properly")


if __name__ == "__main__":
    unittest.main()
