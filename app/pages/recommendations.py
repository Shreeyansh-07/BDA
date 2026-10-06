import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from app.services.recommender import recommender_service
from app.components.movie_card import render_movie_card

def render_recommendations():
    """Renders personalized recommendations feed in Netflix styling."""
    user = st.session_state.get("user")
    user_id = user["id"] if user else 1
    username = user["username"] if user else "User 1"

    taste = recommender_service.get_user_taste_profile(user_id)
    liked_titles = taste["liked_titles"]

    # Context Header
    st.markdown(f"""
    <div style="margin-bottom: 1.5rem;">
        <div style="font-size: 0.8rem; font-weight: 700; color: #e50914; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.3rem;">
            APACHE SPARK COLLABORATIVE FILTERING
        </div>
        <div style="font-size: 2.2rem; font-weight: 900; color: #fff;">
            Recommended For {username}
        </div>
    </div>
    """, unsafe_allow_html=True)

    if liked_titles:
        chips_str = " • ".join(liked_titles[:4])
        st.markdown(f"""
        <div style="background: #14151a; border: 1px solid rgba(255,255,255,0.07); padding: 0.85rem 1.25rem; border-radius: 8px; margin-bottom: 1.5rem; font-size: 0.88rem; color: #8e90a0;">
            Based on your high ratings for: <strong style="color: #fff;">{chips_str}</strong>
        </div>
        """, unsafe_allow_html=True)
    elif taste["is_als_user"]:
        st.markdown(f"""
        <div style="background: #14151a; border: 1px solid rgba(255,255,255,0.07); padding: 0.85rem 1.25rem; border-radius: 8px; margin-bottom: 1.5rem; font-size: 0.88rem; color: #8e90a0;">
            Predictions calculated from User {user_id}'s latent vector representations in the trained Spark ALS model.
        </div>
        """, unsafe_allow_html=True)

    # Number of titles
    col_s, _ = st.columns([3, 7])
    with col_s:
        num_titles = st.select_slider("Recommendation Batch Size", options=[6, 12, 18, 24], value=12)

    recs = recommender_service.recommend_movies(user_id=user_id, n=num_titles)

    if not recs:
        st.info("No recommendations found.")
        return

    # 6 columns grid matching inspiration
    cols_per_row = 6
    for i in range(0, len(recs), cols_per_row):
        batch = recs[i:i + cols_per_row]
        cols = st.columns(cols_per_row)
        for idx, m in enumerate(batch):
            with cols[idx]:
                render_movie_card(m, key_prefix=f"rec_page_{i}_{idx}")

if __name__ == "__main__":
    import sys
    from pathlib import Path
    ROOT_DIR = Path(__file__).resolve().parent.parent.parent
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))
    import streamlit as st
    st.set_page_config(page_title="MovieMind | Recommendations", page_icon="🎬", layout="wide", initial_sidebar_state="expanded")
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
    render_recommendations()
