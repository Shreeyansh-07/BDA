import streamlit as st

def render_navbar():
    """Renders the top navigation bar matching the Netflix design in download.jpg."""
    user = st.session_state.get("user")
    current_page = st.session_state.get("current_page", "Home")

    col_brand, col_links, col_user = st.columns([2.2, 5.8, 3.0])

    with col_brand:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 0.5rem; padding-top: 0.3rem;">
            <span style="color: #e50914; font-size: 1.6rem; font-weight: 900; letter-spacing: 0.08em; cursor: pointer;">MOVIEMIND</span>
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
        for idx, (label, target) in enumerate(pages_def):
            with nav_cols[idx]:
                is_active = (current_page == target)
                dot = " •" if is_active else ""
                if st.button(f"{label}{dot}", key=f"nav_top_{target}", use_container_width=True):
                    st.session_state["current_page"] = target
                    st.rerun()

    with col_user:
        if user:
            col_prof, col_out = st.columns([1.4, 1.0])
            with col_prof:
                display_name = user.get("username", "Account")
                if st.button(f"👤 {display_name}", key="nav_user_profile_btn", use_container_width=True):
                    st.session_state["current_page"] = "Profile"
                    st.rerun()
            with col_out:
                if st.button("🚪 Logout", key="nav_logout_btn", use_container_width=True):
                    st.session_state["user"] = None
                    st.session_state["current_page"] = "Home"
                    st.toast("Logged out successfully.", icon="👋")
                    st.rerun()
        else:
            if st.button("🔑 Sign In / Sign Up", key="nav_signin_btn", use_container_width=True):
                st.session_state["current_page"] = "Profile"
                st.rerun()

    st.markdown("<hr style='margin: 0.6rem 0 1.6rem 0; border: none; border-bottom: 1px solid rgba(255,255,255,0.07);'>", unsafe_allow_html=True)
