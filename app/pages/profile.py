import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from datetime import datetime
from app.services.users import user_service
from app.services.movies import catalog_service

def render_profile():
    """Renders user authentication, account profile, and rated movies history."""
    user = st.session_state.get("user")

    if user:
        _render_authenticated_profile(user)
    else:
        _render_auth_forms()

def _render_authenticated_profile(user: dict):
    user_id = user["id"]
    username = user["username"]

    st.markdown(f"""
    <div style="margin-bottom: 2rem;">
        <span style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3); color: #34d399; padding: 0.35rem 0.85rem; border-radius: 9999px; font-size: 0.82rem; font-weight: 600;">
            ACTIVE SESSION
        </span>
        <h1 style="font-size: 2.5rem; font-weight: 800; margin: 0.5rem 0 0.2rem 0;">User Profile: {username}</h1>
        <p style="color: #94a3b8; font-size: 0.95rem;">Manage your credentials, view rating history, and watchlist status.</p>
    </div>
    """, unsafe_allow_html=True)

    # User Metrics
    rated_movies = user_service.get_user_rated_movies(user_id)
    watchlist_items = user_service.get_watchlist(user_id)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{user_id}</div>
            <div class="stat-label">User ID</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{len(rated_movies)}</div>
            <div class="stat-label">Movies Rated</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{len(watchlist_items)}</div>
            <div class="stat-label">Watchlist Saved</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
    
    # Rating History Section
    st.markdown("<h3 style='font-size: 1.4rem; color: #fff;'>⭐ My Rating History</h3>", unsafe_allow_html=True)
    if rated_movies:
        for item in rated_movies[:15]:
            m = catalog_service.get_movie(item["movieId"])
            title = m["title"] if m else f"Movie ID {item['movieId']}"
            year = m["year"] if m else ""
            date_str = datetime.fromtimestamp(item["timestamp"]).strftime('%Y-%m-%d %H:%M')
            
            st.markdown(f"""
            <div style="background: rgba(18, 24, 38, 0.6); border: 1px solid rgba(255,255,255,0.06); padding: 0.85rem 1.25rem; border-radius: 10px; margin-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong style="color: #f8fafc; font-size: 1rem;">{title}</strong> <span style="color: #94a3b8; font-size: 0.85rem;">({year})</span>
                    <div style="font-size: 0.75rem; color: #64748b;">Rated on {date_str}</div>
                </div>
                <div style="font-size: 1.2rem; font-weight: 700; color: #fbbf24;">
                    ★ {item['rating']}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("You haven't rated any movies yet. Explore titles and submit ratings to train personalized preferences!")

    st.markdown("<hr style='margin: 2rem 0; border: none; border-bottom: 1px solid rgba(255,255,255,0.08);'>", unsafe_allow_html=True)
    
    # Logout Button
    col_out, _ = st.columns([2, 8])
    with col_out:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state["user"] = None
            st.toast("Logged out successfully.", icon="👋")
            st.rerun()

def _render_auth_forms():
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h1 style="font-size: 2.5rem; font-weight: 800; margin-bottom: 0.2rem;">👤 Account Login & Registration</h1>
        <p style="color: #94a3b8; font-size: 0.95rem;">Authenticate to save personalized ratings, manage your watchlist, and unlock custom ALS recommendations.</p>
    </div>
    """, unsafe_allow_html=True)

    tab_login, tab_register = st.tabs(["🔑 Sign In", "✨ Create New Account"])

    with tab_login:
        st.markdown("<div style='max-width: 450px;'>", unsafe_allow_html=True)
        login_user = st.text_input("Username", key="login_username_input")
        login_pass = st.text_input("Password", type="password", key="login_pass_input")
        if st.button("Sign In", use_container_width=True, key="btn_signin"):
            if not login_user or not login_pass:
                st.error("Please enter both username and password.")
            else:
                success, msg, user_obj = user_service.login(login_user, login_pass)
                if success:
                    st.session_state["user"] = user_obj
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_register:
        st.markdown("<div style='max-width: 450px;'>", unsafe_allow_html=True)
        reg_user = st.text_input("Choose Username", key="reg_username_input")
        reg_pass = st.text_input("Create Password", type="password", key="reg_pass_input")
        reg_pass2 = st.text_input("Confirm Password", type="password", key="reg_pass2_input")
        if st.button("Create Account", use_container_width=True, key="btn_create"):
            if reg_pass != reg_pass2:
                st.error("Passwords do not match.")
            else:
                success, msg, user_obj = user_service.register(reg_user, reg_pass)
                if success:
                    st.session_state["user"] = user_obj
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    import sys
    from pathlib import Path
    ROOT_DIR = Path(__file__).resolve().parent.parent.parent
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))
    import streamlit as st
    st.set_page_config(page_title="MovieMind | Profile", page_icon="🎬", layout="wide", initial_sidebar_state="expanded")
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
    render_profile()
