import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from app.services.recommender import recommender_service
from app.services.movies import catalog_service
from app.services.users import user_service
from app.components.movie_card import render_movie_card

def render_recommendations():
    """Renders personalized recommendations feed evaluated on the user's Watchlist."""
    user = st.session_state.get("user")
    if not user:
        from app.components.auth_portal import render_auth_portal
        render_auth_portal()
        return

    user_id = user.get("id", 1)
    username = user.get("username", "Movie Fan")
    email = user.get("email")

    # Context Header
    st.markdown(f"""
    <div style="margin-bottom: 1.5rem;">
        <div style="font-size: 0.8rem; font-weight: 700; color: #e50914; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.3rem;">
            PERSONALIZED RECOMMENDATION ENGINE
        </div>
        <div style="font-size: 2.2rem; font-weight: 900; color: #fff;">
            Recommended For {username}
        </div>
        <div style="font-size: 0.85rem; color: #94a3b8;">
            Tuned in real-time based on your saved titles in My List and MongoDB Atlas taste evaluation.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Evaluate user's Watchlist
    watchlist_eval = recommender_service.evaluate_watchlist(user_id, email=email)
    wl_count = watchlist_eval["count"]
    wl_genres = watchlist_eval["top_genres"]

    if wl_count > 0:
        genres_str = " • ".join(wl_genres[:4]) if wl_genres else "Your Saved Titles"
        titles_sample = ", ".join([f"'{t}'" for t in watchlist_eval["titles"][:3]])
        st.markdown(f"""
        <div style="background: rgba(229, 9, 20, 0.08); border: 1px solid rgba(229, 9, 20, 0.35); padding: 0.95rem 1.35rem; border-radius: 10px; margin-bottom: 1.5rem;">
            <div style="font-size: 0.76rem; color: #ff4d4d; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;">
                🎯 PERSONAL TASTE EVALUATION • {wl_count} TITLES IN MY LIST
            </div>
            <div style="color: #fff; font-size: 0.95rem; font-weight: 600; margin-top: 0.2rem;">
                Top Affinity Genres: <span style="color: #38bdf8;">{genres_str}</span>
            </div>
            <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 0.2rem;">
                Active seed titles: {titles_sample}{' and more' if wl_count > 3 else ''}. All recommendations below are weighted directly by your saved films.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); padding: 1.1rem 1.35rem; border-radius: 10px; margin-bottom: 1.5rem;">
            <div style="font-size: 0.76rem; color: #fbbf24; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;">
                💡 START CUSTOMIZING YOUR PERSONAL RECOMMENDATIONS
            </div>
            <div style="color: #fff; font-size: 0.95rem; font-weight: 600; margin-top: 0.2rem;">
                Your Watchlist (My List) is currently empty.
            </div>
            <div style="font-size: 0.82rem; color: #cbd5e1; margin-top: 0.2rem;">
                Click <strong>+ List</strong> on any movie card or use the quick-starters below to add movies to your list. Our engine evaluates your saved titles immediately!
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Quick Starter Row to populate watchlist with 1 click
        st.markdown("<h4 style='font-size: 1rem; color: #fff;'>⚡ Popular Starter Picks (Add to My List to Personalize):</h4>", unsafe_allow_html=True)
        starter_ids = [1, 296, 318, 593, 2571, 260] # Toy Story, Pulp Fiction, Shawshank, Silence of Lambs, Matrix, Star Wars
        starter_movies = catalog_service.get_movies_by_ids(starter_ids)
        col_starters = st.columns(6)
        for idx, sm in enumerate(starter_movies):
            with col_starters[idx]:
                render_movie_card(sm, key_prefix=f"rec_starter_{idx}")

        st.markdown("<hr style='margin: 1.8rem 0; border: none; border-bottom: 1px solid rgba(255,255,255,0.08);'>", unsafe_allow_html=True)

    # Number of titles slider & analytics CTA
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
