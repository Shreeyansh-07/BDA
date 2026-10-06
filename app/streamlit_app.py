import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st

# 1. Page Configuration
st.set_page_config(
    page_title="MovieMind | Big Data Movie Recommendations",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inject Custom Cinematic CSS
css_path = Path(__file__).parent / "assets" / "styles.css"
if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# 3. Initialize Session State
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Home"

if "user" not in st.session_state:
    st.session_state["user"] = None

if "selected_movie_id" not in st.session_state:
    st.session_state["selected_movie_id"] = None

if "recently_viewed" not in st.session_state:
    st.session_state["recently_viewed"] = []

# 4. Imports for UI Components & Pages
from app.components.navbar import render_navbar
from app.components.sidebar import render_sidebar
from app.pages.home import render_home
from app.pages.search import render_search
from app.pages.movie_details import render_movie_details
from app.pages.recommendations import render_recommendations
from app.pages.watchlist import render_watchlist
from app.pages.profile import render_profile
from app.pages.analytics import render_analytics

def main():
    # Render Navigation & Sidebar
    render_navbar()
    render_sidebar()

    # Route Page
    page = st.session_state.get("current_page", "Home")

    try:
        if page == "Home":
            render_home()
        elif page == "Search":
            render_search()
        elif page == "Movie Details":
            render_movie_details()
        elif page == "Recommendations":
            render_recommendations()
        elif page == "Watchlist":
            render_watchlist()
        elif page == "Profile":
            render_profile()
        elif page == "System Analytics":
            render_analytics()
        else:
            render_home()
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        st.info("System gracefully recovered. You can return to Home safely.")
        if st.button("Return to Home"):
            st.session_state["current_page"] = "Home"
            st.rerun()

if __name__ == "__main__":
    main()
