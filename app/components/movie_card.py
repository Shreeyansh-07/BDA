import streamlit as st
from app.services.tmdb import tmdb_service
from app.utils.helpers import generate_svg_poster

def render_movie_card(movie: dict, key_prefix: str = ""):
    """
    Renders a movie card strictly modeled after the production Netflix UI in download.jpg:
    - High-res vertical poster (2:3 aspect ratio, rounded corners)
    - Movie title in clean bold sans-serif
    - Sub-line: Year on the left, interaction icons in middle, gold star rating on the right
    - ALS affinity tag if collaborative filtering recommendation
    """
    movie_id = movie["movieId"]
    title = movie.get("title", "Unknown Title")
    year = movie.get("year", "N/A")
    rating = movie.get("avg_rating", movie.get("rating", 4.0))
    genres = movie.get("genres", [])
    genre_display = genres[0] if genres else "Film"
    
    # TMDb poster with cache or fallback
    tmdb_id = movie.get("tmdbId")
    tmdb_info = tmdb_service.get_movie_details(
        tmdb_id=tmdb_id,
        title=title,
        year=year,
        fallback_genres=movie.get("raw_genres", "")
    )
    poster_url = tmdb_info.get("poster_path")
    if not poster_url:
        poster_url = generate_svg_poster(title, year, genre_display)

    # Collaborative filtering ALS score tag
    predicted_score = movie.get("predicted_rating")
    als_badge = f'<div class="als-tag-badge">ALS {predicted_score:.1f}★</div>' if predicted_score else ''

    # Card Markup matching inspiration image
    card_html = f"""
    <div class="poster-card-container">
        <div class="poster-image-box">
            <img src="{poster_url}" alt="{title}" loading="lazy" />
            {als_badge}
        </div>
        <div class="card-details-box">
            <div class="card-movie-title" title="{title}">{title}</div>
            <div class="card-subline">
                <span>{year}</span>
                <span class="card-icons">♥ 👁</span>
                <span class="card-rating-gold">★ {rating:.1f}</span>
            </div>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    # Sleek pill action button
    btn_key = f"btn_card_{key_prefix}_{movie_id}"
    if st.button("▶ Open Details", key=btn_key, use_container_width=True):
        st.session_state["selected_movie_id"] = movie_id
        st.session_state["current_page"] = "Movie Details"
        try:
            st.switch_page("pages/movie_details.py")
        except Exception:
            st.rerun()
