import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from app.services.movies import catalog_service
from app.services.tmdb import tmdb_service
from app.services.users import user_service
from app.services.recommender import recommender_service
from app.components.movie_row import render_movie_row

def render_movie_details():
    """
    Renders the expanded movie details banner strictly matching the
    Jurassic World section in download.jpg.
    """
    user = st.session_state.get("user")
    if not user:
        from app.components.auth_portal import render_auth_portal
        render_auth_portal()
        return

    movie_id = st.session_state.get("selected_movie_id")
    if not movie_id:
        popular = catalog_service.get_popular_movies(limit=1)
        movie_id = popular[0]["movieId"] if popular else 1
        st.session_state["selected_movie_id"] = movie_id

    movie = catalog_service.get_movie(movie_id)
    if not movie:
        st.error(f"Movie with ID {movie_id} was not found.")
        return

    # Track recently viewed
    if "recently_viewed" not in st.session_state:
        st.session_state["recently_viewed"] = []
    if movie_id not in st.session_state["recently_viewed"]:
        st.session_state["recently_viewed"].insert(0, movie_id)
    st.session_state["recently_viewed"] = st.session_state["recently_viewed"][:12]

    # Active user
    user = st.session_state.get("user")
    user_id = user["id"] if user else 1

    # Fetch enriched metadata from TMDb
    tmdb_info = tmdb_service.get_movie_details(
        tmdb_id=movie.get("tmdbId"),
        title=movie["title"],
        year=movie["year"],
        fallback_genres=movie.get("raw_genres", "")
    )

    backdrop_url = tmdb_info.get("backdrop_path") or "https://image.tmdb.org/t/p/w1280/8ZTVqvKDQ8emSGUEMjsS4yHAwrp.jpg"
    genres_str = " | ".join(movie.get("genres", [])[:3])
    runtime_str = tmdb_info.get("runtime", "2h 08m")
    overview_text = tmdb_info.get("overview", "A captivating cinematic journey powered by Big Data collaborative filtering.")

    # Close / Return Bar
    col_close, _ = st.columns([1, 11])
    with col_close:
        if st.button("✕ Close", key="btn_close_details", use_container_width=True):
            st.session_state["current_page"] = "Home"
            st.rerun()

    # 1. Expanded Movie Hero Banner (Strictly matching download.jpg)
    st.markdown(f"""
    <div class="expanded-movie-hero" style="background-image: url('{backdrop_url}');">
        <div class="expanded-overlay">
            <div>
                <div class="hero-meta-badge">Duration: {runtime_str}</div>
                <div class="hero-meta-row">
                    <span class="rating-star-gold">★ {movie.get('avg_rating', 4.5):.1f}</span>
                    <span class="age-badge">13+</span>
                    <span>{genres_str}</span>
                </div>
                <div class="hero-title-text" style="font-size: 2.8rem;">{movie['title']}</div>
                <div class="hero-description" style="max-width: 750px;">{overview_text}</div>
            </div>
            <div>
                <!-- Bottom Subtabs bar matching inspiration image -->
                <div class="expanded-nav-tabs">
                    <div style="font-size: 0.85rem; color: #8e90a0;">
                        Director: <strong style="color: #fff;">{tmdb_info.get('director', 'Acclaimed Director')}</strong>
                    </div>
                    <div style="color: #ffb703; font-weight: 700; font-size: 0.9rem;">
                        Spark ALS Affinity: ★ {recommender_service.predict_rating(user_id, movie_id):.1f}
                    </div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Action Controls (Watch & Add List)
    email = user.get("email") if user else None
    in_watchlist = user_service.is_in_watchlist(user_id, movie_id, email=email)
    col_play, col_wl, col_rate_btn, col_blank = st.columns([1.6, 1.8, 2.2, 4.4])
    with col_play:
        if st.button("▶ WATCH NOW", key="details_watch_btn", use_container_width=True):
            st.toast(f"Playing '{movie['title']}'", icon="🎬")
    with col_wl:
        wl_label = "✓ IN LIST" if in_watchlist else "+ ADD LIST"
        if st.button(wl_label, key="details_add_list_btn", use_container_width=True):
            if not user:
                st.toast("Please sign in or register with your Mail ID to save your Watchlist!", icon="🔑")
                st.session_state["current_page"] = "Profile"
                st.rerun()
            elif in_watchlist:
                user_service.remove_from_watchlist(user_id, movie_id, email=email)
                st.toast("Removed from My List", icon="🗑️")
            else:
                user_service.add_to_watchlist(user_id, movie_id, email=email)
                st.toast("Added to My List", icon="📑")
            st.rerun()
    with col_rate_btn:
        user_curr_rating = user_service.get_user_rating(user_id, movie_id, email=email)
        rate_str = f"Your Rating: {user_curr_rating}★" if user_curr_rating else "Rate Movie"
        st.markdown(f"<div style='text-align: center; padding-top: 0.4rem; color: #ffb703; font-weight: 600; font-size: 0.85rem;'>{rate_str}</div>", unsafe_allow_html=True)

    # 3. Sub-tabs Navigation (Matching download.jpg: GENERAL INFORMATION | WATCH TRAILER | SIMILAR | REVIEWS & DETAILS)
    tab_info, tab_trailer, tab_similar, tab_rate = st.tabs([
        "GENERAL INFORMATION",
        "WATCH TRAILER",
        "SIMILAR TITLES",
        "RATE & REVIEWS"
    ])

    with tab_info:
        col_cast, col_meta = st.columns([6, 4])
        with col_cast:
            st.markdown("<h4 style='font-size: 1rem; color: #fff;'>Starring Cast</h4>", unsafe_allow_html=True)
            cast_list = tmdb_info.get("cast", [])
            if cast_list:
                st.write(", ".join(cast_list[:6]))
            else:
                st.write("Featured MovieLens Ensemble Cast")
            
            st.markdown("<h4 style='font-size: 1rem; color: #fff; margin-top: 1rem;'>Full Synopsis</h4>", unsafe_allow_html=True)
            st.write(overview_text)

        with col_meta:
            st.markdown(f"""
            <div style="background: #14151a; border: 1px solid rgba(255,255,255,0.07); padding: 1.25rem; border-radius: 8px;">
                <div style="font-size: 0.8rem; color: #8e90a0; margin-bottom: 0.4rem;">RELEASE YEAR: <strong style="color: #fff;">{movie['year']}</strong></div>
                <div style="font-size: 0.8rem; color: #8e90a0; margin-bottom: 0.4rem;">RUNTIME: <strong style="color: #fff;">{runtime_str}</strong></div>
                <div style="font-size: 0.8rem; color: #8e90a0; margin-bottom: 0.4rem;">GENRES: <strong style="color: #fff;">{genres_str}</strong></div>
                <div style="font-size: 0.8rem; color: #8e90a0; margin-bottom: 0.4rem;">MOVIELENS ID: <strong style="color: #fff;">{movie_id}</strong></div>
                <div style="font-size: 0.8rem; color: #8e90a0;">TMDB ID: <strong style="color: #fff;">{tmdb_info.get('tmdb_id', 'N/A')}</strong></div>
            </div>
            """, unsafe_allow_html=True)

    with tab_trailer:
        trailer_key = tmdb_info.get("trailer_key")
        if trailer_key:
            st.video(f"https://www.youtube.com/watch?v={trailer_key}")
        else:
            st.info("No trailer video link found for this title.")

    with tab_similar:
        similar_movies = recommender_service.similar_movies(movie_id, n=6)
        render_movie_row(
            title="✨ Titles Similar to This",
            movies=similar_movies,
            subtitle="Content Cosine Similarity",
            key_prefix="similar_details",
            cols_per_row=6
        )

    with tab_rate:
        st.markdown("<h4 style='font-size: 1rem; color: #fff;'>Rate this Movie</h4>", unsafe_allow_html=True)
        new_val = st.slider("Your Rating (1.0 to 5.0 stars)", min_value=1.0, max_value=5.0, value=float(user_curr_rating or 4.0), step=0.5)
        if st.button("Save Rating", key="btn_save_rating_details"):
            user_service.rate_movie(user_id, movie_id, new_val, email=email)
            st.success(f"Rating {new_val}★ saved to database!")
            st.rerun()

if __name__ == "__main__":
    import sys
    from pathlib import Path
    ROOT_DIR = Path(__file__).resolve().parent.parent.parent
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))
    import streamlit as st
    st.set_page_config(page_title="MovieMind | Movie Details", page_icon="🎬", layout="wide", initial_sidebar_state="expanded")
    css_path = Path(__file__).resolve().parent.parent / "assets" / "styles.css"
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    if "user" not in st.session_state:
        st.session_state["user"] = {"id": 1, "username": "User_1", "created_at": "2026-10-06"}
    if "selected_movie_id" not in st.session_state or not st.session_state["selected_movie_id"]:
        st.session_state["selected_movie_id"] = 1
    if "recently_viewed" not in st.session_state:
        st.session_state["recently_viewed"] = []
    from app.components.navbar import render_navbar
    from app.components.sidebar import render_sidebar
    render_navbar()
    render_sidebar()
    render_movie_details()
