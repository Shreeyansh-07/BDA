import sys
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
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
    user_id = user.get("id", 1)
    username = user.get("username", "Movie Fan")
    email = user.get("email", "N/A")
    source = user.get("source", "MongoDB Atlas")

    st.markdown(f"""
    <div style="margin-bottom: 2rem;">
        <span style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3); color: #34d399; padding: 0.35rem 0.85rem; border-radius: 9999px; font-size: 0.82rem; font-weight: 700;">
            ACTIVE SESSION • {source.upper()}
        </span>
        <h1 style="font-size: 2.5rem; font-weight: 800; margin: 0.5rem 0 0.2rem 0; color: #fff;">
            User Profile: {username}
        </h1>
        <p style="color: #94a3b8; font-size: 0.95rem;">
            Email: <strong style="color: #fff;">{email}</strong> | Account ID: <code style="color: #38bdf8;">{user_id}</code> | Connected to MongoDB Atlas.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # User Metrics
    rated_movies = user_service.get_user_rated_movies(user_id, email=email)
    watchlist_items = user_service.get_watchlist(user_id, email=email)

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
            <div class="stat-value" style="color: #fbbf24;">{len(rated_movies)}</div>
            <div class="stat-label">Movies Rated</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value" style="color: #e50914;">{len(watchlist_items)}</div>
            <div class="stat-label">Watchlist Saved</div>
        </div>
        """, unsafe_allow_html=True)

    # Quick Action Buttons
    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    col_act1, col_act2, _ = st.columns([2.5, 2.5, 5])
    with col_act1:
        if st.button("🍿 View My Watchlist", use_container_width=True):
            st.session_state["current_page"] = "Watchlist"
            st.rerun()
    with col_act2:
        if st.button("🎯 My Recommendations", use_container_width=True):
            st.session_state["current_page"] = "Recommendations"
            st.rerun()

    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
    
    # Rating History Section
    st.markdown("<h3 style='font-size: 1.3rem; color: #fff;'>⭐ My Rating History</h3>", unsafe_allow_html=True)
    if rated_movies:
        for item in rated_movies[:15]:
            m = catalog_service.get_movie(item["movieId"])
            title = m["title"] if m else f"Movie ID {item['movieId']}"
            year = m["year"] if m else ""
            ts = item.get("timestamp")
            date_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M') if ts else "Recent"
            
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
        st.info("You haven't rated any movies yet. Rate titles to further sharpen your personal recommendations!")

    st.markdown("<hr style='margin: 2rem 0; border: none; border-bottom: 1px solid rgba(255,255,255,0.08);'>", unsafe_allow_html=True)
    
    # Logout Button
    col_out, _ = st.columns([2, 8])
    with col_out:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state["user"] = None
            st.toast("Logged out successfully.", icon="👋")
            st.rerun()

def _render_auth_forms():
    mongo_status = "🟢 MongoDB Atlas Online" if user_service.is_mongo_online() else "🟠 Local Database Mode"
    
    st.markdown(f"""
    <div style="margin-bottom: 1.8rem;">
        <span style="background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.3); color: #34d399; padding: 0.3rem 0.75rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 600;">
            {mongo_status}
        </span>
        <h1 style="font-size: 2.4rem; font-weight: 900; margin: 0.5rem 0 0.2rem 0; color: #fff;">
            👤 User Authentication
        </h1>
        <p style="color: #94a3b8; font-size: 0.95rem;">
            Sign in with your Mail ID or create a new account. Your watchlist and personal recommendations are stored securely in MongoDB!
        </p>
    </div>
    """, unsafe_allow_html=True)

    tab_login, tab_register = st.tabs(["🔑 Sign In", "✨ Sign Up (New Account)"])

    # 1. Sign In Tab
    with tab_login:
        st.markdown("<div style='max-width: 480px;'>", unsafe_allow_html=True)
        login_ident = st.text_input("Mail ID or Username", key="login_ident_input", placeholder="e.g. keshav@gmail.com")
        login_pass = st.text_input("Password", type="password", key="login_pass_input", placeholder="Enter your password")
        
        if st.button("Sign In", use_container_width=True, key="btn_signin"):
            if not login_ident or not login_pass:
                st.error("Please enter both your mail ID / username and password.")
            else:
                success, msg, user_obj = user_service.login(login_ident, login_pass)
                if success:
                    st.session_state["user"] = user_obj
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
        st.markdown("</div>", unsafe_allow_html=True)

    # 2. Sign Up Tab (Takes mail id and password)
    with tab_register:
        st.markdown("<div style='max-width: 480px;'>", unsafe_allow_html=True)
        reg_email = st.text_input("Mail ID *", key="reg_email_input", placeholder="e.g. user@example.com")
        reg_username = st.text_input("Username (Optional)", key="reg_username_input", placeholder="Leave blank to use email prefix")
        reg_pass = st.text_input("Create Password *", type="password", key="reg_pass_input", placeholder="At least 4 characters")
        reg_pass2 = st.text_input("Confirm Password *", type="password", key="reg_pass2_input", placeholder="Re-enter password")
        
        if st.button("✨ Create Account & Store in DB", use_container_width=True, key="btn_create"):
            if not reg_email or not reg_pass:
                st.error("Mail ID and Password are required.")
            elif reg_pass != reg_pass2:
                st.error("Passwords do not match.")
            else:
                success, msg, user_obj = user_service.register(
                    email=reg_email,
                    password=reg_pass,
                    username=reg_username
                )
                if success:
                    st.session_state["user"] = user_obj
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    st.set_page_config(page_title="MovieMind | Profile", page_icon="🎬", layout="wide")
    render_profile()
