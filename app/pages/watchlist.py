import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from app.services.users import user_service
from app.services.movies import catalog_service
from app.services.recommender import recommender_service
from app.components.movie_card import render_movie_card

def render_watchlist():
    """Renders user's saved watchlist with 6 columns and evaluates personal recommendations from it."""
    user = st.session_state.get("user")
    user_id = user["id"] if user else None
    username = user.get("username", "Guest") if user else "Guest"
    email = user.get("email") if user else None

    st.markdown(f"""
    <div style="margin-bottom: 1.5rem;">
        <div style="font-size: 2.2rem; font-weight: 900; color: #fff;">
            My List ({username})
        </div>
        <div style="font-size: 0.85rem; color: #94a3b8;">
            Synchronized with MongoDB Atlas. Every title you save here directly refines your personalized recommendations.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not user:
        st.markdown("""
        <div style="background: #14151a; border: 1px solid rgba(255,255,255,0.07); padding: 2.5rem 1.5rem; text-align: center; border-radius: 8px;">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🔒</div>
            <h3 style="color: #fff; margin-bottom: 0.5rem;">Sign In to Save Your Watchlist</h3>
            <p style="color: #8e90a0; max-width: 500px; margin: 0 auto 1.5rem auto;">
                Create an account or log in with your Mail ID so you can access your saved movies anytime and receive personalized recommendations.
            </p>
        </div>
        """, unsafe_allow_html=True)
        col_btn, _ = st.columns([3, 7])
        with col_btn:
            if st.button("🔑 Sign In / Sign Up", use_container_width=True, key="wl_login_btn"):
                st.session_state["current_page"] = "Profile"
                st.rerun()
        return

    movie_ids = user_service.get_watchlist(user_id, email=email)
    if not movie_ids:
        st.markdown("""
        <div style="background: #14151a; border: 1px solid rgba(255,255,255,0.07); padding: 3rem 1.5rem; text-align: center; border-radius: 8px;">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🍿</div>
            <h3 style="color: #fff; margin-bottom: 0.5rem;">Your List is Empty</h3>
            <p style="color: #8e90a0;">Click "+ ADD LIST" on any title to save movies here and trigger customized recommendations.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # Watchlist Grid
    movies = catalog_service.get_movies_by_ids(movie_ids)
    cols_per_row = 6
    for i in range(0, len(movies), cols_per_row):
        batch = movies[i:i + cols_per_row]
        cols = st.columns(cols_per_row)
        for idx, m in enumerate(batch):
            with cols[idx]:
                render_movie_card(m, key_prefix=f"watchlist_{i}_{idx}")

    # Watchlist Evaluated Personal Recommendations Section
    st.markdown("<hr style='margin: 2.5rem 0 1.5rem 0; border: none; border-bottom: 1px solid rgba(255,255,255,0.08);'>", unsafe_allow_html=True)
    st.markdown("""
    <div style="margin-bottom: 1.2rem;">
        <span style="background: rgba(229, 9, 20, 0.15); border: 1px solid rgba(229, 9, 20, 0.3); color: #ff4d4d; padding: 0.3rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">
            WATCHLIST TASTE ENGINE
        </span>
        <h2 style="font-size: 1.6rem; font-weight: 800; color: #fff; margin: 0.4rem 0 0.1rem 0;">
            🎯 Recommended Because of What's In Your List
        </h2>
        <div style="font-size: 0.85rem; color: #8e90a0;">
            Personalized recommendations evaluated directly from the movies in your Watchlist above.
        </div>
    </div>
    """, unsafe_allow_html=True)

    recs_from_wl = recommender_service.recommend_from_watchlist(user_id, n=6, email=email)
    if recs_from_wl:
        cols_rec = st.columns(6)
        for idx, rm in enumerate(recs_from_wl):
            with cols_rec[idx]:
                render_movie_card(rm, key_prefix=f"wl_rec_{idx}")
    else:
        st.info("Add more titles to your Watchlist to unlock additional personalized suggestions.")

if __name__ == "__main__":
    st.set_page_config(page_title="MovieMind | My List", page_icon="🎬", layout="wide")
    render_watchlist()
