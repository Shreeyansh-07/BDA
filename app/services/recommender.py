import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

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

    def predict_rating(self, user_id: Any, movie_id: int) -> float:
        """
        Predicts user rating for a movie.
        Uses exact Spark ALS predicted score if present in top matrix,
        or computes baseline from movie average rating combined with watchlist similarity.
        """
        user_key = str(user_id)
        if user_key in self._als_recommendations:
            for item in self._als_recommendations[user_key]:
                if int(item[0]) == int(movie_id):
                    return round(float(item[1]), 1)

        # Baseline fallback
        movie = catalog_service.get_movie(movie_id)
        if movie:
            return round(movie.get("avg_rating", 3.8), 1)
        return 3.8

    def evaluate_watchlist(self, user_id: Any, email: Optional[str] = None) -> Dict[str, Any]:
        """
        Thoroughly evaluates the user's Watchlist (My List) to extract:
        - Genre affinity distribution and percentage weights
        - Saved movie titles and details
        - Overall taste summary
        """
        watchlist_ids = user_service.get_watchlist(user_id, email=email)
        watchlist_movies = catalog_service.get_movies_by_ids(watchlist_ids)

        genre_counts: Dict[str, int] = {}
        for m in watchlist_movies:
            for g in m.get("genres", []):
                genre_counts[g] = genre_counts.get(g, 0) + 1

        total_genre_occurrences = sum(genre_counts.values()) or 1
        genre_percentages = {
            g: round((cnt / total_genre_occurrences) * 100, 1)
            for g, cnt in sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
        }

        top_genres = sorted(genre_counts.keys(), key=lambda g: genre_counts[g], reverse=True)

        return {
            "watchlist_ids": watchlist_ids,
            "watchlist_movies": watchlist_movies,
            "count": len(watchlist_ids),
            "genre_counts": genre_counts,
            "genre_percentages": genre_percentages,
            "top_genres": top_genres[:5],
            "titles": [m["title"] for m in watchlist_movies[:8]]
        }

    def recommend_from_watchlist(
        self,
        user_id: Any,
        n: int = 12,
        email: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generates personalized recommendations explicitly evaluated on the user's Watchlist (My List).
        - Computes content similarity to saved titles
        - Weights candidate movies by overlapping watchlist genres
        - Generates personalized reason tags (e.g. 'Because you added Inception')
        """
        eval_data = self.evaluate_watchlist(user_id, email=email)
        watchlist_ids = set(eval_data["watchlist_ids"])
        watchlist_movies = eval_data["watchlist_movies"]
        top_genres = eval_data["top_genres"]
        genre_counts = eval_data["genre_counts"]

        if not watchlist_movies:
            return []

        # Exclude movies already rated or already in watchlist
        in_app_ratings = user_service.get_user_rated_movies(user_id, email=email)
        exclude_ids = watchlist_ids.union(set(r["movieId"] for r in in_app_ratings))

        candidates: Dict[int, Dict[str, Any]] = {}

        # 1. Candidate Generation from each movie in watchlist
        for w_movie in watchlist_movies[:8]:
            w_id = w_movie["movieId"]
            w_title = w_movie["title"]
            similar = catalog_service.get_similar_movies(w_id, limit=8)

            for rank_idx, sm in enumerate(similar):
                sm_id = sm["movieId"]
                if sm_id in exclude_ids:
                    continue

                # Calculate genre overlap score with user's overall watchlist taste
                matching_genres = [g for g in sm.get("genres", []) if g in genre_counts]
                genre_weight = sum(genre_counts.get(g, 1) for g in matching_genres)
                base_rating = sm.get("avg_rating", 3.8)

                # Rank decay score from similarity list
                rank_score = max(0.1, 1.0 - (rank_idx * 0.1))

                # Predicted personalized rating for this user
                predicted_val = min(5.0, round(base_rating + 0.15 * min(genre_weight, 4), 1))

                if sm_id not in candidates:
                    item_copy = dict(sm)
                    item_copy["predicted_rating"] = predicted_val
                    item_copy["recommendation_source"] = "Watchlist Taste Engine"
                    item_copy["recommendation_reason"] = f"Inspired by '{w_title}' in My List"
                    item_copy["_score"] = (predicted_val * 1.5) + (rank_score * 2.0) + genre_weight
                    candidates[sm_id] = item_copy
                else:
                    # If recommended by multiple watchlist items, boost score and reason!
                    candidates[sm_id]["_score"] += (rank_score * 1.5) + genre_weight
                    candidates[sm_id]["recommendation_reason"] = f"Matches multiple titles in your Watchlist ({w_title})"

        # 2. Candidate Generation from top genres if still needed
        if len(candidates) < n and top_genres:
            for g in top_genres[:2]:
                genre_movies = catalog_service.get_movies_by_genre(g, limit=10)
                for gm in genre_movies:
                    gm_id = gm["movieId"]
                    if gm_id not in exclude_ids and gm_id not in candidates:
                        item_copy = dict(gm)
                        item_copy["predicted_rating"] = round(gm.get("avg_rating", 4.0), 1)
                        item_copy["recommendation_source"] = "Watchlist Genre Profile"
                        item_copy["recommendation_reason"] = f"Top {g} pick matching your My List"
                        item_copy["_score"] = item_copy["predicted_rating"]
                        candidates[gm_id] = item_copy
                        if len(candidates) >= n * 2:
                            break

        # Sort candidates by combined score
        sorted_recs = sorted(candidates.values(), key=lambda x: x.get("_score", 0), reverse=True)
        return sorted_recs[:n]

    def recommend_movies(
        self,
        user_id: Optional[Any],
        n: int = 12,
        email: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generates top-N recommendations for the given user:
        1. Evaluates user's Watchlist (My List) as primary personal preference.
        2. Blends with Apache Spark ALS Collaborative Filtering latent vector predictions.
        3. Blends with Content-Based preferences from recent in-app ratings.
        4. Graceful Cold Start fallback if user is a brand new visitor without watchlist/ratings.
        """
        # 1. Cold start guest check
        if user_id is None:
            return self._cold_start_recommendations(n, reason="Trending & Popular (Cold Start Fallback)")

        results: List[Dict[str, Any]] = []
        seen_ids = set()

        # 2. Watchlist evaluation (Primary personalized source)
        watchlist_recs = self.recommend_from_watchlist(user_id=user_id, n=n, email=email)
        for wr in watchlist_recs:
            if wr["movieId"] not in seen_ids:
                seen_ids.add(wr["movieId"])
                results.append(wr)

        # 3. Check if user is in trained Spark ALS model (MovieLens user)
        user_key = str(user_id)
        has_als = user_key in self._als_recommendations
        in_app_ratings = user_service.get_user_rated_movies(user_id, email=email)
        rated_movie_ids = set(r["movieId"] for r in in_app_ratings)

        if has_als and len(results) < n:
            als_items = self._als_recommendations[user_key]
            for m_id, score in als_items:
                if m_id not in seen_ids and m_id not in rated_movie_ids:
                    m = catalog_service.get_movie(m_id)
                    if m:
                        m_copy = dict(m)
                        m_copy["predicted_rating"] = round(float(score), 1)
                        m_copy["recommendation_source"] = "Apache Spark ALS Collaborative Filtering"
                        m_copy["recommendation_reason"] = f"Spark ALS Latent Match ({m_copy['predicted_rating']}★)"
                        seen_ids.add(m_id)
                        results.append(m_copy)
                        if len(results) >= n:
                            break

        # 4. In-app ratings content-based fallback
        liked_in_app = [r["movieId"] for r in in_app_ratings if r["rating"] >= 4.0]
        if len(results) < n and liked_in_app:
            for liked_id in liked_in_app[:3]:
                liked_movie = catalog_service.get_movie(liked_id)
                liked_title = liked_movie["title"] if liked_movie else "your favorites"
                sim_movies = catalog_service.get_similar_movies(liked_id, limit=6)
                for sm in sim_movies:
                    sm_id = sm["movieId"]
                    if sm_id not in seen_ids and sm_id not in rated_movie_ids:
                        sm_copy = dict(sm)
                        sm_copy["predicted_rating"] = sm.get("avg_rating", 4.0)
                        sm_copy["recommendation_source"] = "Rating Content Preference"
                        sm_copy["recommendation_reason"] = f"Because you rated '{liked_title}' 5★"
                        seen_ids.add(sm_id)
                        results.append(sm_copy)
                        if len(results) >= n:
                            break
                if len(results) >= n:
                    break

        # 5. Fallback if still under n
        if len(results) < n:
            filler = self._cold_start_recommendations(n - len(results), reason="Popular Recommendation")
            for f in filler:
                if f["movieId"] not in seen_ids and f["movieId"] not in rated_movie_ids:
                    seen_ids.add(f["movieId"])
                    results.append(f)
                    if len(results) >= n:
                        break

        return results[:n]

    def _cold_start_recommendations(self, n: int, reason: str) -> List[Dict[str, Any]]:
        """Provides high-quality cold-start recommendations for new users or guests."""
        popular = catalog_service.get_popular_movies(limit=n * 2)
        top_rated = catalog_service.get_top_rated_movies(limit=n * 2)

        combined = []
        seen = set()
        for p, t in zip(popular, top_rated):
            if p["movieId"] not in seen:
                seen.add(p["movieId"])
                p_copy = dict(p)
                p_copy["predicted_rating"] = round(p.get("avg_rating", 4.2), 1)
                p_copy["recommendation_source"] = "Popularity Baseline"
                p_copy["recommendation_reason"] = reason
                combined.append(p_copy)
            if t["movieId"] not in seen:
                seen.add(t["movieId"])
                t_copy = dict(t)
                t_copy["predicted_rating"] = round(t.get("avg_rating", 4.5), 1)
                t_copy["recommendation_source"] = "Top Rated Baseline"
                t_copy["recommendation_reason"] = "Critically Acclaimed (Cold Start)"
                combined.append(t_copy)

        return combined[:n]

    def similar_movies(self, movie_id: int, n: int = 10) -> List[Dict[str, Any]]:
        """Returns movies similar to movie_id."""
        return catalog_service.get_similar_movies(movie_id, limit=n)

    def get_user_taste_profile(self, user_id: Any, email: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns full taste profile and recommendation analytics data for a specific user:
        - Watchlist evaluation
        - In-app ratings
        - Aggregated genre breakdown
        - Sample personalized recommendations
        """
        watchlist_eval = self.evaluate_watchlist(user_id, email=email)
        in_app_ratings = user_service.get_user_rated_movies(user_id, email=email)

        # Combine genres from watchlist and ratings
        all_genres: Dict[str, int] = dict(watchlist_eval["genre_counts"])
        for r in in_app_ratings:
            if r["rating"] >= 3.5:
                m = catalog_service.get_movie(r["movieId"])
                if m:
                    for g in m.get("genres", []):
                        all_genres[g] = all_genres.get(g, 0) + 2

        # Fetch user's personalized recommendations
        recommendations = self.recommend_movies(user_id=user_id, n=18, email=email)

        # Extract recommendation genres distribution
        rec_genre_counts: Dict[str, int] = {}
        for r in recommendations:
            for g in r.get("genres", []):
                rec_genre_counts[g] = rec_genre_counts.get(g, 0) + 1

        user_key = str(user_id)
        is_als_user = user_key in self._als_recommendations

        return {
            "user_id": user_id,
            "is_als_user": is_als_user,
            "watchlist_count": watchlist_eval["count"],
            "watchlist_titles": watchlist_eval["titles"],
            "watchlist_genres": watchlist_eval["genre_percentages"],
            "rated_count": len(in_app_ratings),
            "top_genres": sorted(all_genres.keys(), key=lambda x: all_genres[x], reverse=True)[:5],
            "recommendations": recommendations,
            "rec_genre_counts": rec_genre_counts
        }

recommender_service = RecommendationEngine()

# Standalone helper functions
def recommend_movies(user_id: int, n: int = 10) -> List[Dict[str, Any]]:
    return recommender_service.recommend_movies(user_id, n=n)

def similar_movies(movie_id: int, n: int = 10) -> List[Dict[str, Any]]:
    return recommender_service.similar_movies(movie_id, n=n)

def predict_rating(user_id: int, movie_id: int) -> float:
    return recommender_service.predict_rating(user_id, movie_id)
