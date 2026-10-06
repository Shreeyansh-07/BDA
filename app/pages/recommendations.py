import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from app.services.recommender import recommender_service
from app.components.movie_card import render_movie_card

def render_recommendations():
    """Renders personalized recommendations feed in Netflix styling, evaluated on user's Watchlist."""
    user = st.session_state.get("user")
    user_id = user["id"] if user else None
    username = user.get("username", "Guest") if user else "Guest"
    email = user.get("email") if user else None

    # Context Header
    st.markdown(f"""
    <div style="margin-bottom: 1.5rem;">
        <div style="font-size: 0.8rem; font-weight: 700; color: #e50914; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.3rem;">
            PERSONALIZED RECOMMENDATION ENGINE
        </div>
        <div style="font-size: 2.2rem; font-weight: 900; color: #fff;">
            Recommended For {username}
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not user:
        st.markdown("""
        <div style="background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.25); padding: 1rem 1.25rem; border-radius: 8px; margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: center;">
            <div style="color: #cbd5e1; font-size: 0.9rem;">
                🔑 <strong>Not signed in?</strong> Create an account with your Mail ID to save your personal Watchlist in MongoDB and unlock custom ALS recommendations!
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Sign In / Sign Up Now", key="rec_login_prompt"):
            st.session_state["current_page"] = "Profile"
            st.rerun()

    # Evaluate user's Watchlist
    watchlist_eval = recommender_service.evaluate_watchlist(user_id, email=email) if user_id else {"count": 0, "titles": [], "top_genres": []}
    wl_count = watchlist_eval["count"]
    wl_genres = watchlist_eval["top_genres"]

    if wl_count > 0:
        genres_str = " • ".join(wl_genres[:4]) if wl_genres else "Your Saved Titles"
        st.markdown(f"""
        <div style="background: #14151a; border: 1px solid rgba(229, 9, 20, 0.3); padding: 0.85rem 1.25rem; border-radius: 8px; margin-bottom: 1.5rem; font-size: 0.88rem; color: #8e90a0;">
            🍿 <strong>Evaluated from your Watchlist ({wl_count} saved):</strong> Top genres: <strong style="color: #fff;">{genres_str}</strong>
        </div>
        """, unsafe_allow_html=True)
    elif user:
        st.markdown("""
        <div style="background: #14151a; border: 1px solid rgba(255,255,255,0.07); padding: 0.85rem 1.25rem; border-radius: 8px; margin-bottom: 1.5rem; font-size: 0.88rem; color: #8e90a0;">
            💡 <em>Your Watchlist is empty.</em> Add films to <strong>My List</strong> with "+ ADD LIST" on any title to customize these recommendations instantly!
        </div>
        """, unsafe_allow_html=True)

    # Number of titles slider & filter
    col_s, col_ana = st.columns([4, 6])
    with col_s:
        num_titles = st.select_slider("Recommendation Batch Size", options=[6, 12, 18, 24], value=12)
    with col_ana:
        st.markdown("<div style='padding-top: 1.6rem;'></div>", unsafe_allow_html=True)
        if st.button("📊 View Personalized Analytics (Bar, Pie, Box Plot)", key="rec_jump_analytics"):
            st.session_state["current_page"] = "System Analytics"
            st.rerun()

    recs = recommender_service.recommend_movies(user_id=user_id, n=num_titles, email=email)

    if not recs:
        st.info("No recommendations found.")
        return

    # 6 columns grid matching Netflix inspiration
    cols_per_row = 6
    for i in range(0, len(recs), cols_per_row):
        batch = recs[i:i + cols_per_row]
        cols = st.columns(cols_per_row)
        for idx, m in enumerate(batch):
            with cols[idx]:
                render_movie_card(m, key_prefix=f"rec_page_{i}_{idx}")

if __name__ == "__main__":
    st.set_page_config(page_title="MovieMind | Recommendations", page_icon="🎬", layout="wide")
    render_recommendations()
