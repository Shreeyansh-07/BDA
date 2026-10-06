import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from app.services.users import user_service
from app.services.movies import catalog_service
from app.components.movie_card import render_movie_card

def render_watchlist():
    """Renders user's saved watchlist with 6 columns."""
    user = st.session_state.get("user")
    user_id = user["id"] if user else 1
    username = user["username"] if user else "User 1"

    st.markdown(f"""
    <div style="margin-bottom: 1.5rem;">
        <div style="font-size: 2.2rem; font-weight: 900; color: #fff;">
            My List ({username})
        </div>
    </div>
    """, unsafe_allow_html=True)

    movie_ids = user_service.get_watchlist(user_id)
    if not movie_ids:
        st.markdown("""
        <div style="background: #14151a; border: 1px solid rgba(255,255,255,0.07); padding: 3rem 1.5rem; text-align: center; border-radius: 8px;">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🍿</div>
            <h3 style="color: #fff; margin-bottom: 0.5rem;">Your List is Empty</h3>
            <p style="color: #8e90a0;">Click "+ ADD LIST" on any title to save movies here.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    movies = catalog_service.get_movies_by_ids(movie_ids)
    cols_per_row = 6
    for i in range(0, len(movies), cols_per_row):
        batch = movies[i:i + cols_per_row]
        cols = st.columns(cols_per_row)
        for idx, m in enumerate(batch):
            with cols[idx]:
                render_movie_card(m, key_prefix=f"watchlist_{i}_{idx}")

if __name__ == "__main__":
    import sys
    from pathlib import Path
    ROOT_DIR = Path(__file__).resolve().parent.parent.parent
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))
    import streamlit as st
    st.set_page_config(page_title="MovieMind | My List", page_icon="🎬", layout="wide", initial_sidebar_state="expanded")
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
    render_watchlist()
