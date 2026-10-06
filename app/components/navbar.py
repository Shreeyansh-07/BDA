import streamlit as st

def render_navbar():
    """Renders the top navigation bar matching the Netflix design in download.jpg."""
    user = st.session_state.get("user")
    current_page = st.session_state.get("current_page", "Home")

    col_brand, col_links, col_user = st.columns([2.5, 6, 2.5])

    with col_brand:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 0.5rem; padding-top: 0.3rem;">
            <span style="color: #e50914; font-size: 1.6rem; font-weight: 900; letter-spacing: 0.08em;">MOVIEMIND</span>
        </div>
        """, unsafe_allow_html=True)

    with col_links:
        # Centered navigation buttons styled horizontally
        nav_cols = st.columns(5)
        pages_def = [
            ("Home", "Home"),
            ("Movies", "Search"),
            ("Recommendations", "Recommendations"),
            ("My List", "Watchlist"),
            ("Analytics", "System Analytics"),
        ]
        PAGE_NAV_MAP = {
            "Home": "pages/home.py",
            "Search": "pages/search.py",
            "Recommendations": "pages/recommendations.py",
            "Watchlist": "pages/watchlist.py",
            "System Analytics": "pages/analytics.py",
            "Profile": "pages/profile.py",
        }
        for idx, (label, target) in enumerate(pages_def):
            with nav_cols[idx]:
                is_active = (current_page == target)
                dot = " •" if is_active else ""
                if st.button(f"{label}{dot}", key=f"nav_top_{target}", use_container_width=True):
                    st.session_state["current_page"] = target
                    try:
                        st.switch_page(PAGE_NAV_MAP.get(target, "pages/home.py"))
                    except Exception:
                        st.rerun()

    with col_user:
        if user:
            display_name = user.get("username", "Account")
            if st.button(f"👤 {display_name}", key="nav_user_profile_btn", use_container_width=True):
                st.session_state["current_page"] = "Profile"
                try:
                    st.switch_page("pages/profile.py")
                except Exception:
                    st.rerun()
        else:
            if st.button("🔑 Sign In / Sign Up", key="nav_signin_btn", use_container_width=True):
                st.session_state["current_page"] = "Profile"
                try:
                    st.switch_page("pages/profile.py")
                except Exception:
                    st.rerun()

    st.markdown("<hr style='margin: 0.6rem 0 1.6rem 0; border: none; border-bottom: 1px solid rgba(255,255,255,0.07);'>", unsafe_allow_html=True)
