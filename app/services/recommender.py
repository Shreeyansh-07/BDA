import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from config.config import MODELS_DIR
from app.services.movies import catalog_service
from app.services.users import user_service

class RecommendationEngine:
    def __init__(self):
        self._als_recommendations: Dict[str, List[List[Any]]] = {}
        self.load_precomputed_recs()

    def load_precomputed_recs(self):
        """Loads precomputed ALS top recommendations from disk for sub-millisecond serving."""
        rec_file = MODELS_DIR / "als_recommendations.json"
        if rec_file.exists():
            try:
                with open(rec_file, "r", encoding="utf-8") as f:
                    self._als_recommendations = json.load(f)
            except Exception:
                self._als_recommendations = {}

    def predict_rating(self, user_id: int, movie_id: int) -> float:
        """
        Predicts user rating for a movie.
        Uses exact Spark ALS predicted score if present in top matrix,
        or computes baseline from movie average rating.
        """
        user_key = str(user_id)
        if user_key in self._als_recommendations:
            for item in self._als_recommendations[user_key]:
                if int(item[0]) == int(movie_id):
                    return round(float(item[1]), 1)

        # Baseline fallback
        movie = catalog_service.get_movie(movie_id)
        if movie:
            return round(movie.get("avg_rating", 3.5), 1)
        return 3.5

    def recommend_movies(self, user_id: Optional[int], n: int = 10) -> List[Dict[str, Any]]:
        """
        Generates top-N recommendations for the given user.
        - Existing user in Spark ALS: Returns ALS Collaborative Filtering predictions.
        - User with recent in-app ratings: Blends ALS with content recommendations from rated titles.
        - Cold start (new user or guest): Popular + Top Rated fallback with clear reason.
        """
        # 1. Cold start check
        if not user_id or user_id <= 0:
            return self._cold_start_recommendations(n, reason="Trending & Popular (Cold Start Fallback)")

        # 2. Check if user has active in-app ratings in SQLite DB
        in_app_ratings = user_service.get_user_rated_movies(user_id)
        liked_in_app = [r["movieId"] for r in in_app_ratings if r["rating"] >= 4.0]
        rated_movie_ids = set(r["movieId"] for r in in_app_ratings)

        user_key = str(user_id)
        has_als = user_key in self._als_recommendations

        results = []

        # 3. If user has ALS profile
        if has_als:
            als_items = self._als_recommendations[user_key]
            for m_id, score in als_items:
                if m_id not in rated_movie_ids:
                    m = catalog_service.get_movie(m_id)
                    if m:
                        m_copy = dict(m)
                        m_copy["predicted_rating"] = round(float(score), 1)
                        m_copy["recommendation_source"] = "Apache Spark ALS Collaborative Filtering"
                        m_copy["recommendation_reason"] = f"ALS Predicted Score: {m_copy['predicted_rating']} ★"
                        results.append(m_copy)
                        if len(results) >= n:
                            break

        # 4. If user is a new registered user but has rated movies in web app
        if len(results) < n and liked_in_app:
            for liked_id in liked_in_app[:3]:
                liked_movie = catalog_service.get_movie(liked_id)
                liked_title = liked_movie["title"] if liked_movie else "your favorites"
                sim_movies = catalog_service.get_similar_movies(liked_id, limit=5)
                for sm in sim_movies:
                    sm_id = sm["movieId"]
                    if sm_id not in rated_movie_ids and not any(r["movieId"] == sm_id for r in results):
                        sm_copy = dict(sm)
                        sm_copy["predicted_rating"] = sm.get("avg_rating", 4.0)
                        sm_copy["recommendation_source"] = "Content-Based Preference"
                        sm_copy["recommendation_reason"] = f"Because you rated '{liked_title}' highly"
                        results.append(sm_copy)
                        if len(results) >= n:
                            break
                if len(results) >= n:
                    break

        # 5. Fallback if still under n
        if len(results) < n:
            filler = self._cold_start_recommendations(n - len(results), reason="Popular Recommendation")
            for f in filler:
                if f["movieId"] not in rated_movie_ids and not any(r["movieId"] == f["movieId"] for r in results):
                    results.append(f)
                    if len(results) >= n:
                        break

        return results[:n]

    def _cold_start_recommendations(self, n: int, reason: str) -> List[Dict[str, Any]]:
        """Provides high-quality cold-start recommendations for new users or guests."""
        popular = catalog_service.get_popular_movies(limit=n * 2)
        top_rated = catalog_service.get_top_rated_movies(limit=n * 2)
        
        # Interleave popular and top rated
        combined = []
        seen = set()
        for p, t in zip(popular, top_rated):
            if p["movieId"] not in seen:
                seen.add(p["movieId"])
                p_copy = dict(p)
                p_copy["recommendation_source"] = "Popularity Baseline"
                p_copy["recommendation_reason"] = reason
                combined.append(p_copy)
            if t["movieId"] not in seen:
                seen.add(t["movieId"])
                t_copy = dict(t)
                t_copy["recommendation_source"] = "Top Rated Baseline"
                t_copy["recommendation_reason"] = "Critically Acclaimed (Cold Start)"
                combined.append(t_copy)

        return combined[:n]

    def similar_movies(self, movie_id: int, n: int = 10) -> List[Dict[str, Any]]:
        """Returns movies similar to movie_id."""
        return catalog_service.get_similar_movies(movie_id, limit=n)

    def get_user_taste_profile(self, user_id: int) -> Dict[str, Any]:
        """Returns summary of user's liked movies and genres for personalized UI display."""
        in_app_ratings = user_service.get_user_rated_movies(user_id)
        liked_movies = []
        top_genres = {}

        for r in in_app_ratings:
            if r["rating"] >= 4.0:
                m = catalog_service.get_movie(r["movieId"])
                if m:
                    liked_movies.append(m["title"])
                    for g in m["genres"]:
                        top_genres[g] = top_genres.get(g, 0) + 1

        # If user is in MovieLens dataset (user 1 to 610)
        user_key = str(user_id)
        is_als_user = user_key in self._als_recommendations

        sorted_genres = sorted(top_genres.items(), key=lambda x: x[1], reverse=True)
        return {
            "user_id": user_id,
            "is_als_user": is_als_user,
            "rated_count": len(in_app_ratings),
            "liked_titles": liked_movies[:5],
            "top_genres": [g[0] for g in sorted_genres[:3]]
        }

recommender_service = RecommendationEngine()

# Standalone helper functions as required by specification
def recommend_movies(user_id: int, n: int = 10) -> List[Dict[str, Any]]:
    return recommender_service.recommend_movies(user_id, n=n)

def similar_movies(movie_id: int, n: int = 10) -> List[Dict[str, Any]]:
    return recommender_service.similar_movies(movie_id, n=n)

def predict_rating(user_id: int, movie_id: int) -> float:
    return recommender_service.predict_rating(user_id, movie_id)
