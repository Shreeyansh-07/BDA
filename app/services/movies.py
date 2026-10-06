import re
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from config.config import DATA_DIR

class MovieCatalogService:
    def __init__(self):
        self._movies_df: Optional[pd.DataFrame] = None
        self._movie_dict: Dict[int, Dict[str, Any]] = {}
        self._genres_list: List[str] = []
        self._top_rated_ids: List[int] = []
        self._popular_ids: List[int] = []
        self._trending_ids: List[int] = []
        self._genre_movie_map: Dict[str, List[int]] = {}
        self._content_sim_matrix: Optional[np.ndarray] = None
        self._movie_id_to_idx: Dict[int, int] = {}
        self._idx_to_movie_id: Dict[int, int] = {}
        self.load_data()

    def load_data(self):
        movies_path = DATA_DIR / "movies.csv"
        links_path = DATA_DIR / "links.csv"
        ratings_path = DATA_DIR / "ratings.csv"

        if not movies_path.exists():
            return

        # Read movies
        movies_df = pd.read_csv(movies_path)
        
        # Merge links if available
        if links_path.exists():
            try:
                links_df = pd.read_csv(links_path)
                movies_df = movies_df.merge(links_df, on="movieId", how="left")
            except Exception:
                movies_df["tmdbId"] = np.nan
        else:
            movies_df["tmdbId"] = np.nan

        # Extract Year & Clean Title
        years = []
        clean_titles = []
        year_pattern = re.compile(r"\((\d{4})\)")
        for title in movies_df["title"]:
            match = year_pattern.search(str(title))
            if match:
                years.append(match.group(1))
                clean_titles.append(re.sub(r"\s*\(\d{4}\)\s*", "", str(title)).strip())
            else:
                years.append("Unknown")
                clean_titles.append(str(title).strip())

        movies_df["year"] = years
        movies_df["clean_title"] = clean_titles

        # Calculate rating statistics if ratings.csv exists
        if ratings_path.exists():
            try:
                ratings_df = pd.read_csv(ratings_path)
                stats = ratings_df.groupby("movieId").agg(
                    avg_rating=("rating", "mean"),
                    rating_count=("rating", "count")
                ).reset_index()
                movies_df = movies_df.merge(stats, on="movieId", how="left")
                movies_df["avg_rating"] = movies_df["avg_rating"].fillna(3.5).round(1)
                movies_df["rating_count"] = movies_df["rating_count"].fillna(0).astype(int)
            except Exception:
                movies_df["avg_rating"] = 3.8
                movies_df["rating_count"] = 50
        else:
            movies_df["avg_rating"] = 3.8
            movies_df["rating_count"] = 50

        self._movies_df = movies_df

        # Build Quick Lookup Dictionary
        all_genres = set()
        for _, row in movies_df.iterrows():
            m_id = int(row["movieId"])
            raw_genres = str(row["genres"]) if pd.notna(row["genres"]) else ""
            g_list = [g.strip() for g in raw_genres.split("|") if g.strip() and g != "(no genres listed)"]
            for g in g_list:
                all_genres.add(g)

            tmdb_id = int(row["tmdbId"]) if pd.notna(row.get("tmdbId")) and str(row.get("tmdbId")).replace('.', '').isdigit() else None

            self._movie_dict[m_id] = {
                "movieId": m_id,
                "title": row["clean_title"],
                "full_title": row["title"],
                "year": row["year"],
                "genres": g_list,
                "raw_genres": raw_genres,
                "tmdbId": tmdb_id,
                "avg_rating": float(row["avg_rating"]),
                "rating_count": int(row["rating_count"])
            }

        self._genres_list = sorted(list(all_genres))

        # Precompute Curated Lists
        # Popular movies (highest count)
        pop_df = movies_df.sort_values(by=["rating_count", "avg_rating"], ascending=[False, False])
        self._popular_ids = pop_df["movieId"].head(50).astype(int).tolist()

        # Top Rated (min 30 ratings, sorted by rating)
        top_df = movies_df[movies_df["rating_count"] >= 30].sort_values(by=["avg_rating", "rating_count"], ascending=[False, False])
        if len(top_df) < 20:
            top_df = movies_df.sort_values(by="avg_rating", ascending=False)
        self._top_rated_ids = top_df["movieId"].head(50).astype(int).tolist()

        # Trending movies (mix of recent years and popularity)
        recent_df = movies_df[movies_df["year"].astype(str).str.isdigit()]
        if not recent_df.empty:
            recent_sorted = recent_df.sort_values(by=["year", "rating_count"], ascending=[False, False])
            self._trending_ids = recent_sorted["movieId"].head(50).astype(int).tolist()
        else:
            self._trending_ids = self._popular_ids[:50]

        # Genre Map
        for g in self._genres_list:
            g_df = movies_df[movies_df["genres"].str.contains(g, case=False, na=False)].sort_values(
                by=["rating_count", "avg_rating"], ascending=[False, False]
            )
            self._genre_movie_map[g] = g_df["movieId"].head(40).astype(int).tolist()

        # Build fast content-based similarity index using genres
        self._build_content_index()

    def _build_content_index(self):
        """Builds one-hot genre vectors to quickly compute similar movies."""
        if self._movies_df is None or self._movies_df.empty:
            return
        
        movie_ids = list(self._movie_dict.keys())
        self._movie_id_to_idx = {m_id: i for i, m_id in enumerate(movie_ids)}
        self._idx_to_movie_id = {i: m_id for i, m_id in enumerate(movie_ids)}

        num_movies = len(movie_ids)
        num_genres = len(self._genres_list)
        if num_genres == 0:
            return

        genre_to_idx = {g: i for i, g in enumerate(self._genres_list)}
        feature_matrix = np.zeros((num_movies, num_genres), dtype=np.float32)

        for i, m_id in enumerate(movie_ids):
            for g in self._movie_dict[m_id]["genres"]:
                if g in genre_to_idx:
                    feature_matrix[i, genre_to_idx[g]] = 1.0

        # Normalize rows for cosine similarity
        norms = np.linalg.norm(feature_matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self._normalized_features = feature_matrix / norms

    def get_movie(self, movie_id: int) -> Optional[Dict[str, Any]]:
        return self._movie_dict.get(int(movie_id))

    def get_movies_by_ids(self, movie_ids: List[int]) -> List[Dict[str, Any]]:
        results = []
        for mid in movie_ids:
            m = self.get_movie(mid)
            if m:
                results.append(m)
        return results

    def get_popular_movies(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self.get_movies_by_ids(self._popular_ids[:limit])

    def get_top_rated_movies(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self.get_movies_by_ids(self._top_rated_ids[:limit])

    def get_trending_movies(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self.get_movies_by_ids(self._trending_ids[:limit])

    def get_movies_by_genre(self, genre: str, limit: int = 10) -> List[Dict[str, Any]]:
        m_ids = self._genre_movie_map.get(genre, [])
        return self.get_movies_by_ids(m_ids[:limit])

    def get_all_genres(self) -> List[str]:
        return self._genres_list

    def search_movies(
        self,
        query: str = "",
        genre: Optional[str] = None,
        year: Optional[str] = None,
        min_rating: float = 0.0,
        sort_by: str = "Popularity",
        limit: int = 40
    ) -> List[Dict[str, Any]]:
        """Filters and searches movies matching user specifications."""
        if self._movies_df is None:
            return []

        df = self._movies_df.copy()

        if query:
            q = query.strip().lower()
            df = df[df["title"].str.lower().str.contains(q, na=False)]

        if genre and genre != "All":
            df = df[df["genres"].str.contains(genre, case=False, na=False)]

        if year and year != "All":
            df = df[df["year"] == str(year)]

        if min_rating > 0:
            df = df[df["avg_rating"] >= min_rating]

        if sort_by == "Popularity":
            df = df.sort_values(by="rating_count", ascending=False)
        elif sort_by == "Highest Rated":
            df = df.sort_values(by=["avg_rating", "rating_count"], ascending=[False, False])
        elif sort_by == "Newest":
            df = df.sort_values(by="year", ascending=False)
        elif sort_by == "Title (A-Z)":
            df = df.sort_values(by="clean_title", ascending=True)

        matched_ids = df["movieId"].head(limit).astype(int).tolist()
        return self.get_movies_by_ids(matched_ids)

    def get_similar_movies(self, movie_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Finds content-similar movies based on genre vector cosine similarity."""
        if movie_id not in self._movie_id_to_idx or self._normalized_features is None:
            # Fallback to genre-matching
            m = self.get_movie(movie_id)
            if m and m["genres"]:
                first_genre = m["genres"][0]
                candidates = [c for c in self._genre_movie_map.get(first_genre, []) if c != movie_id]
                return self.get_movies_by_ids(candidates[:limit])
            return self.get_popular_movies(limit)

        idx = self._movie_id_to_idx[movie_id]
        target_vec = self._normalized_features[idx]
        sim_scores = np.dot(self._normalized_features, target_vec)

        # Do not recommend the same movie
        sim_scores[idx] = -1.0

        top_indices = np.argsort(sim_scores)[::-1][:limit]
        similar_ids = [self._idx_to_movie_id[i] for i in top_indices if sim_scores[i] > 0]
        return self.get_movies_by_ids(similar_ids)

# Global Singleton
catalog_service = MovieCatalogService()
