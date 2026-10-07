import streamlit as st
from app.services.tmdb import tmdb_service
from app.services.users import user_service
from app.utils.helpers import generate_svg_poster

def render_movie_card(movie: dict, key_prefix: str = ""):
    """
    Renders a movie card strictly modeled after the production Netflix UI in download.jpg:
    - High-res vertical poster (2:3 aspect ratio, rounded corners)
    - Movie title in clean bold sans-serif
    - Sub-line: Year on the left, interaction icons in middle, gold star rating on the right
    - Personal recommendation tag (e.g. 'Inspired by Inception in My List' or 'ALS 4.5★')
    - Dual quick-action buttons: '▶ Details' and '+ List' / '✓ In List'
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

    # Recommendation badge
    predicted_score = movie.get("predicted_rating")
    reason = movie.get("recommendation_reason")
    if reason:
        # Truncate reason if too long for card badge
        short_reason = reason if len(reason) <= 24 else reason[:22] + "…"
        badge_html = f'<div class="als-tag-badge" title="{reason}">{short_reason}</div>'
    elif predicted_score:
        badge_html = f'<div class="als-tag-badge">★ {predicted_score:.1f}</div>'
    else:
        badge_html = ''

    # Card Markup matching inspiration image
    card_html = f"""
    <div class="poster-card-container">
        <div class="poster-image-box">
            <img src="{poster_url}" alt="{title}" loading="lazy" />
            {badge_html}
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

    # User & Watchlist state
    user = st.session_state.get("user")
    user_id = user.get("id", 1) if user else None
    email = user.get("email") if user else None

    # Dual quick-action buttons
    col_det, col_wl = st.columns([1.1, 1.0])
    with col_det:
        btn_key = f"btn_card_{key_prefix}_{movie_id}"
        if st.button("▶ Info", key=btn_key, use_container_width=True):
            st.session_state["selected_movie_id"] = movie_id
            st.session_state["current_page"] = "Movie Details"
            st.rerun()

    with col_wl:
        if user_id:
            in_list = user_service.is_in_watchlist(user_id, movie_id, email=email)
            wl_label = "✓ List" if in_list else "+ List"
            wl_key = f"btn_wl_{key_prefix}_{movie_id}"
            if st.button(wl_label, key=wl_key, use_container_width=True):
                if in_list:
                    user_service.remove_from_watchlist(user_id, movie_id, email=email)
                    st.toast(f"Removed '{title}' from My List", icon="🗑️")
                else:
                    user_service.add_to_watchlist(user_id, movie_id, email=email)
                    st.toast(f"Added '{title}' to My List (MongoDB)", icon="📑")
                st.rerun()
        else:
            if st.button("+ List", key=f"btn_wl_anon_{key_prefix}_{movie_id}", use_container_width=True):
                st.session_state["current_page"] = "Profile"
                st.rerun()
