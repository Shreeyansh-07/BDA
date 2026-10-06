import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from app.services.movies import catalog_service
from app.services.recommender import recommender_service
from app.services.tmdb import tmdb_service
from app.services.users import user_service
from app.components.movie_row import render_movie_row
from app.components.movie_card import render_movie_card

def render_home():
    """Renders the Netflix-style homepage matching download.jpg."""
    user = st.session_state.get("user")
    user_id = user["id"] if user else 1

    # 1. Featured Hero Banner (Matching the top banner in download.jpg)
    # Pick a critically acclaimed blockbuster for the hero (e.g. Inception or The Dark Knight)
    popular_movies = catalog_service.get_popular_movies(limit=10)
    featured = popular_movies[0] if popular_movies else None
    
    if featured:
        f_tmdb = tmdb_service.get_movie_details(
            tmdb_id=featured.get("tmdbId"),
            title=featured["title"],
            year=featured["year"],
            fallback_genres=featured.get("raw_genres", "")
        )
        backdrop_url = f_tmdb.get("backdrop_path") or "https://image.tmdb.org/t/p/w1280/8ZTVqvKDQ8emSGUEMjsS4yHAwrp.jpg"
        genres_str = " | ".join(featured.get("genres", [])[:3])
        runtime_str = f_tmdb.get("runtime", "2h 15m")
        overview_text = f_tmdb.get("overview", "A cinematic masterpiece exploring complex narratives and distributed collaborative recommendations.")

        st.markdown(f"""
        <div class="hero-wrapper" style="background-image: url('{backdrop_url}');">
            <div class="hero-overlay">
                <div class="hero-meta-badge">Duration: {runtime_str}</div>
                <div class="hero-meta-row">
                    <span class="rating-star-gold">★ {featured.get('avg_rating', 4.5):.1f}</span>
                    <span class="age-badge">13+</span>
                    <span>{genres_str}</span>
                </div>
                <div class="hero-title-text">{featured['title']}</div>
                <div class="hero-description">{overview_text}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Hero Action Buttons
        col_w, col_add, col_space = st.columns([1.8, 1.8, 6.4])
        with col_w:
            if st.button("▶ WATCH", key="hero_watch_btn", use_container_width=True):
                st.session_state["selected_movie_id"] = featured["movieId"]
                st.session_state["current_page"] = "Movie Details"
                st.rerun()
        with col_add:
            in_list = user_service.is_in_watchlist(user_id, featured["movieId"])
            btn_label = "✓ IN LIST" if in_list else "+ ADD LIST"
            if st.button(btn_label, key="hero_add_list_btn", use_container_width=True):
                if in_list:
                    user_service.remove_from_watchlist(user_id, featured["movieId"])
                    st.toast("Removed from My List", icon="🗑️")
                else:
                    user_service.add_to_watchlist(user_id, featured["movieId"])
                    st.toast("Added to My List", icon="📑")
                st.rerun()

    # 2. Category Filter Pills (Matching the genre pills in download.jpg)
    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
    all_genres = ["Action", "Adventure", "Animation", "Comedy", "Crime", "Drama", "Horror", "Mystery", "Romance", "Sci-Fi", "Thriller"]
    
    active_genre = st.session_state.get("home_active_genre", "Action")
    genre_cols = st.columns(len(all_genres))
    for idx, g in enumerate(all_genres):
        with genre_cols[idx]:
            is_sel = (g == active_genre)
            prefix = "🔴 " if is_sel else ""
            if st.button(f"{prefix}{g}", key=f"genre_pill_btn_{g}", use_container_width=True):
                st.session_state["home_active_genre"] = g
                st.rerun()

    # 3. Section 1: "📈 Trends Now" (6 columns)
    genre_selection = st.session_state.get("home_active_genre", "Action")
    trending_genre_movies = catalog_service.get_movies_by_genre(genre_selection, limit=6)
    render_movie_row(
        title=f"📈 Trends Now: {genre_selection}",
        movies=trending_genre_movies,
        subtitle="Trending",
        key_prefix="trends_home",
        cols_per_row=6
    )

    # 4. Section 2: "⚡ Recommended For You (Apache Spark ALS)" (6 columns)
    user_name = user["username"] if user else "User 1"
    recs = recommender_service.recommend_movies(user_id=user_id, n=6)
    render_movie_row(
        title=f"⚡ Recommended For You ({user_name})",
        movies=recs,
        subtitle="Collaborative Filtering",
        key_prefix="spark_recs_home",
        cols_per_row=6
    )

    # 5. Section 3: "🏆 Critically Acclaimed (Top Rated)" (6 columns)
    top_rated = catalog_service.get_top_rated_movies(limit=6)
    render_movie_row(
        title="🏆 Critically Acclaimed",
        movies=top_rated,
        subtitle="Top Rated",
        key_prefix="top_rated_home",
        cols_per_row=6
    )

    # 6. Section 4: "🍿 Popular Movies" (6 columns)
    popular = catalog_service.get_popular_movies(limit=6)
    render_movie_row(
        title="🍿 Popular Movies",
        movies=popular,
        subtitle="All Time",
        key_prefix="popular_home",
        cols_per_row=6
    )

    # 7. Recently Viewed (if any)
    recent_ids = st.session_state.get("recently_viewed", [])
    if recent_ids:
        recent_movies = catalog_service.get_movies_by_ids(recent_ids[:6])
        if recent_movies:
            render_movie_row(
                title="🕒 Recently Viewed",
                movies=recent_movies,
                subtitle="History",
                key_prefix="recent_home",
                cols_per_row=6
            )

if __name__ == "__main__":
    import sys
    from pathlib import Path
    ROOT_DIR = Path(__file__).resolve().parent.parent.parent
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))
    import streamlit as st
    st.set_page_config(page_title="MovieMind | Home", page_icon="🎬", layout="wide", initial_sidebar_state="expanded")
    css_path = Path(__file__).resolve().parent.parent / "assets" / "styles.css"
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    if "user" not in st.session_state:
        st.session_state["user"] = {"id": 1, "username": "User_1", "created_at": "2026-10-06"}
    if "selected_movie_id" not in st.session_state:
        st.session_state["selected_movie_id"] = 1
    if "recently_viewed" not in st.session_state:
        st.session_state["recently_viewed"] = []
    from app.components.navbar import render_navbar
    from app.components.sidebar import render_sidebar
    render_navbar()
    render_sidebar()
    render_home()
