import streamlit as st

PAGES = [
    ("Home", "Home"),
    ("Discover Movies", "Search"),
    ("Recommendations", "Recommendations"),
    ("My List", "Watchlist"),
    ("Account / Sign In", "Profile"),
    ("System Analytics", "System Analytics"),
]

def render_sidebar():
    """Renders the sidebar with academic simulation tools and status."""
    with st.sidebar:
        st.markdown("""
        <div style="margin-bottom: 1.5rem; padding-top: 0.5rem;">
            <div style="color: #e50914; font-size: 1.4rem; font-weight: 900; letter-spacing: 0.08em;">MOVIEMIND</div>
            <div style="font-size: 0.72rem; color: #8e90a0; font-weight: 600; text-transform: uppercase;">Apache Spark ALS Engine</div>
        </div>
        """, unsafe_allow_html=True)

        current_page = st.session_state.get("current_page", "Home")
        
        nav_options = [p[1] for p in PAGES]
        nav_labels = [p[0] for p in PAGES]
        if st.session_state.get("selected_movie_id"):
            nav_options.insert(2, "Movie Details")
            nav_labels.insert(2, "Movie Details")

        selected_idx = 0
        if current_page in nav_options:
            selected_idx = nav_options.index(current_page)

        selected_nav = st.radio(
            "Navigate",
            options=nav_options,
            format_func=lambda opt: nav_labels[nav_options.index(opt)],
            index=selected_idx,
            label_visibility="collapsed"
        )
        if selected_nav != current_page:
            st.session_state["current_page"] = selected_nav
            PAGE_SIDEBAR_MAP = {
                "Home": "pages/home.py",
                "Discover Movies": "pages/search.py",
                "Search": "pages/search.py",
                "Movie Details": "pages/movie_details.py",
                "Recommendations": "pages/recommendations.py",
                "My List": "pages/watchlist.py",
                "Watchlist": "pages/watchlist.py",
                "Account / Sign In": "pages/profile.py",
                "Profile": "pages/profile.py",
                "System Analytics": "pages/analytics.py",
            }
            try:
                st.switch_page(PAGE_SIDEBAR_MAP.get(selected_nav, "pages/home.py"))
            except Exception:
                st.rerun()

        st.markdown("<hr style='margin: 1.5rem 0; border: none; border-bottom: 1px solid rgba(255,255,255,0.07);'>", unsafe_allow_html=True)

        # Active User Session Display
        user = st.session_state.get("user")
        if user:
            u_email = user.get("email", "")
            u_name = user.get("username", "Movie Fan")
            st.markdown(f"""
            <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 6px; padding: 0.65rem 0.85rem; margin-bottom: 1rem;">
                <div style="font-size: 0.72rem; color: #34d399; font-weight: 700;">🟢 LOGGED IN</div>
                <div style="color: #fff; font-weight: 700; font-size: 0.88rem;">{u_name}</div>
                <div style="color: #94a3b8; font-size: 0.75rem; word-break: break-all;">{u_email}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🚪 Logout", key="sidebar_logout_btn", use_container_width=True):
                st.session_state["user"] = None
                st.rerun()
        else:
            st.markdown("""
            <div style="background: rgba(229, 9, 20, 0.08); border: 1px solid rgba(229, 9, 20, 0.25); border-radius: 6px; padding: 0.65rem 0.85rem; margin-bottom: 1rem;">
                <div style="font-size: 0.72rem; color: #ff4d4d; font-weight: 700;">👤 GUEST SESSION</div>
                <div style="color: #94a3b8; font-size: 0.78rem;">Sign in with your Mail ID to save watchlist and personal recs.</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🔑 Sign In / Sign Up", key="sidebar_signin_btn", use_container_width=True):
                st.session_state["current_page"] = "Profile"
                st.rerun()

        # Academic User Simulator
        st.markdown("<div style='font-size: 0.8rem; font-weight: 700; color: #fff; margin-bottom: 0.4rem;'>USER SIMULATOR</div>", unsafe_allow_html=True)
        st.caption("Switch between trained MovieLens users or test cold-start fallback:")
        sim_user = st.selectbox(
            "Active User Profile",
            options=[1, 12, 34, 148, 200, 318, 496, 610, "New User (Cold Start)"],
            index=0,
            key="sim_user_select"
        )
        if st.button("Apply Profile", use_container_width=True):
            if sim_user == "New User (Cold Start)":
                st.session_state["user"] = {
                    "id": 999999,
                    "username": "ColdStart_Guest",
                    "email": "coldstart@guest.com",
                    "created_at": "2026-10-06"
                }
                st.toast("Active profile: New User (Testing Cold Start)", icon="❄️")
            else:
                st.session_state["user"] = {
                    "id": int(sim_user),
                    "username": f"User_{sim_user}",
                    "email": f"user{sim_user}@movielens.org",
                    "created_at": "2026-10-06"
                }
                st.toast(f"Active profile: User {sim_user} (Testing Spark ALS)", icon="⚡")
            st.rerun()

        st.markdown("<hr style='margin: 1.5rem 0; border: none; border-bottom: 1px solid rgba(255,255,255,0.07);'>", unsafe_allow_html=True)
        
        # Engine Metrics
        st.markdown("""
        <div style="background: #14151a; padding: 0.85rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.07); font-size: 0.75rem;">
            <div style="font-weight: 700; color: #e50914; margin-bottom: 0.4rem; letter-spacing: 0.05em;">BIG DATA PIPELINE</div>
            <div style="color: #34d399;">• Database: MongoDB Atlas</div>
            <div style="color: #8e90a0;">• Model: Spark MLlib ALS</div>
            <div style="color: #8e90a0;">• HDFS: Configured</div>
            <div style="color: #8e90a0;">• 32M Benchmark RMSE: ~0.81</div>
        </div>
        """, unsafe_allow_html=True)
