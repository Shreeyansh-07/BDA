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
    """Renders user's saved watchlist and evaluates personal recommendations from it."""
    user = st.session_state.get("user")
    if not user:
        from app.components.auth_portal import render_auth_portal
        render_auth_portal()
        return

    user_id = user.get("id", 1)
    username = user.get("username", "Movie Fan")
    email = user.get("email")

    st.markdown(f"""
    <div style="margin-bottom: 1.5rem;">
        <div style="font-size: 2.2rem; font-weight: 900; color: #fff;">
            My List ({username})
        </div>
        <div style="font-size: 0.85rem; color: #94a3b8;">
            Synchronized in real-time with MongoDB Atlas. Every title you save here directly refines your personalized recommendations.
        </div>
    </div>
    """, unsafe_allow_html=True)

    movie_ids = user_service.get_watchlist(user_id, email=email)
    if not movie_ids:
        st.markdown("""
        <div style="background: #14151a; border: 1px solid rgba(255,255,255,0.07); padding: 2.5rem 1.5rem; text-align: center; border-radius: 12px; margin-bottom: 2rem;">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🍿</div>
            <h3 style="color: #fff; margin-bottom: 0.5rem;">Your Watchlist is Empty</h3>
            <p style="color: #8e90a0; max-width: 550px; margin: 0 auto 1.5rem auto;">
                Click <strong>+ List</strong> on any film below or across the catalog to save movies to MongoDB. Our engine will immediately evaluate your taste!
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<h4 style='font-size: 1.1rem; color: #fff;'>✨ Recommended Starters (Add to My List to Personalize):</h4>", unsafe_allow_html=True)
        starter_ids = [1, 296, 318, 593, 2571, 260]
        starter_movies = catalog_service.get_movies_by_ids(starter_ids)
        cols_starters = st.columns(6)
        for idx, sm in enumerate(starter_movies):
            with cols_starters[idx]:
                render_movie_card(sm, key_prefix=f"wl_empty_starter_{idx}")
        return

    # Watchlist Grid
    movies = catalog_service.get_movies_by_ids(movie_ids)
    st.markdown(f"<div style='font-size: 0.9rem; color: #34d399; font-weight: 700; margin-bottom: 0.8rem;'>{len(movies)} saved titles in MongoDB Atlas</div>", unsafe_allow_html=True)
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
