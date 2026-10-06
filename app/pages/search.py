import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from app.services.movies import catalog_service
from app.components.movie_card import render_movie_card

def render_search():
    """Renders the Movies catalog and search grid matching download.jpg."""
    st.markdown("""
    <div style="margin-bottom: 1.2rem;">
        <div style="font-size: 1.6rem; font-weight: 800; color: #fff;">🎬 Discover Movies</div>
    </div>
    """, unsafe_allow_html=True)

    # Search Bar
    initial_q = st.session_state.pop("search_query", "")
    query = st.text_input("Search catalog", value=initial_q, placeholder="Search by title, e.g. Deadpool, Meg, Jurassic, Avengers...", label_visibility="collapsed")

    # Category Pills (Matching download.jpg)
    genres = ["All", "Action", "Adventure", "Animation", "Comedy", "Crime", "Drama", "Horror", "Mystery", "Romance", "Sci-Fi", "Thriller"]
    active_genre = st.session_state.get("search_active_genre", "All")
    
    genre_cols = st.columns(len(genres))
    for idx, g in enumerate(genres):
        with genre_cols[idx]:
            is_active = (g == active_genre)
            prefix = "🔴 " if is_active else ""
            if st.button(f"{prefix}{g}", key=f"search_genre_{g}", use_container_width=True):
                st.session_state["search_active_genre"] = g
                st.rerun()

    # Sort & Rating Bar (Matching the controls bar in download.jpg)
    col_sort, col_year, col_rate = st.columns([3, 3, 4])
    with col_sort:
        sort_by = st.selectbox(
            "Sort by",
            options=["Popularity", "Highest Rated", "Newest", "Title (A-Z)"],
            index=0
        )
    with col_year:
        years = ["All"] + [str(y) for y in range(2025, 1970, -1)]
        selected_year = st.selectbox("Year", options=years, index=0)
    with col_rate:
        min_rating = st.slider("Min Rating (★)", min_value=0.0, max_value=5.0, value=0.0, step=0.5)

    # Search Execution
    genre_filter = None if active_genre == "All" else active_genre
    results = catalog_service.search_movies(
        query=query,
        genre=genre_filter,
        year=selected_year,
        min_rating=min_rating,
        sort_by=sort_by,
        limit=24
    )

    st.markdown(f"""
    <div style="margin: 1.2rem 0 0.8rem 0; font-size: 0.82rem; color: #8e90a0;">
        Showing <strong style="color: #fff;">{len(results)}</strong> titles in catalog
    </div>
    """, unsafe_allow_html=True)

    if not results:
        st.warning("No titles match your criteria.")
        return

    # Render in 6-column grid matching inspiration
    cols_per_row = 6
    for i in range(0, len(results), cols_per_row):
        batch = results[i:i + cols_per_row]
        cols = st.columns(cols_per_row)
        for idx, m in enumerate(batch):
            with cols[idx]:
                render_movie_card(m, key_prefix=f"search_{i}_{idx}")

if __name__ == "__main__":
    import sys
    from pathlib import Path
    ROOT_DIR = Path(__file__).resolve().parent.parent.parent
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))
    import streamlit as st
    st.set_page_config(page_title="MovieMind | Search", page_icon="🎬", layout="wide", initial_sidebar_state="expanded")
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
    render_search()
