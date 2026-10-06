import streamlit as st
from typing import List, Dict, Any
from app.components.movie_card import render_movie_card

def render_movie_row(title: str, movies: List[Dict[str, Any]], subtitle: str = "", key_prefix: str = "row", cols_per_row: int = 6):
    """
    Renders a row of movie cards matching the 6-column grid in download.jpg:
    - Section header with title
    - 6-column horizontal card grid
    """
    st.markdown(f"""
    <div class="section-row-header">
        <div class="section-title-large">{title}</div>
        <div class="sub-tabs-list">
            <span class="sub-tab-item active">{subtitle or 'Popular'}</span>
            <span class="sub-tab-item">Premieres</span>
            <span class="sub-tab-item">Recently Added</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not movies:
        st.info("No titles found for this category.")
        return

    # Render in chunks of 6 columns (matching inspiration image)
    for i in range(0, len(movies), cols_per_row):
        batch = movies[i:i + cols_per_row]
        cols = st.columns(cols_per_row)
        for idx, movie in enumerate(batch):
            with cols[idx]:
                render_movie_card(movie, key_prefix=f"{key_prefix}_{i}_{idx}")
