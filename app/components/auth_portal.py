import streamlit as st
from app.services.users import user_service

def render_auth_portal():
    """
    Renders the mandatory Login / Sign-up gateway for unauthenticated users.
    Users cannot access the recommendation system until they log in or create an account.
    All accounts are stored securely in MongoDB Atlas.
    """
    mongo_online = user_service.is_mongo_online()
    mongo_badge = "🟢 MongoDB Atlas Online" if mongo_online else "🟠 Local Database Mode"

    # Centered Cinematic Login Hero Container
    st.markdown("""
    <style>
    .auth-container {
        max-width: 520px;
        margin: 2rem auto;
        background: #14151a;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 2.5rem 2.2rem;
        box-shadow: 0 16px 36px rgba(0, 0, 0, 0.7);
    }
    .auth-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    .auth-brand {
        color: #e50914;
        font-size: 2.2rem;
        font-weight: 900;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.2rem;
    }
    .auth-tagline {
        color: #cbd5e1;
        font-size: 0.95rem;
        font-weight: 500;
        margin-bottom: 0.75rem;
    }
    .auth-badge {
        display: inline-block;
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.3);
        color: #34d399;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.04em;
    }
    .auth-pill-feature {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        background: rgba(255, 255, 255, 0.04);
        border-radius: 8px;
        padding: 0.5rem 0.8rem;
        margin-top: 0.6rem;
        font-size: 0.8rem;
        color: #94a3b8;
    }
    </style>
    """, unsafe_allow_html=True)

    col_l, col_center, col_r = st.columns([1, 2, 1])

    with col_center:
        st.markdown(f"""
        <div class="auth-header">
            <div class="auth-brand">MOVIEMIND</div>
            <div class="auth-tagline">Big Data Movie Recommendation System</div>
            <div class="auth-badge">{mongo_badge}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background: rgba(229, 9, 20, 0.08); border-left: 3px solid #e50914; padding: 0.75rem 1rem; border-radius: 6px; margin-bottom: 1.5rem; font-size: 0.85rem; color: #cbd5e1;">
            🔒 <strong>Authentication Required:</strong> Please sign in or create an account with your Mail ID to unlock personalized recommendations, your Watchlist, and custom visual analytics.
        </div>
        """, unsafe_allow_html=True)

        tab_login, tab_signup = st.tabs(["🔑 Sign In", "✨ Create Account (Sign Up)"])

        # ── TAB 1: SIGN IN ──
        with tab_login:
            st.markdown("<div style='padding-top: 0.5rem;'></div>", unsafe_allow_html=True)
            login_ident = st.text_input(
                "Mail ID or Username",
                key="portal_login_ident",
                placeholder="e.g. user@example.com"
            )
            login_pass = st.text_input(
                "Password",
                type="password",
                key="portal_login_pass",
                placeholder="Enter your password"
            )

            st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
            if st.button("Sign In & Access Recommendations", type="primary", use_container_width=True, key="portal_btn_signin"):
                if not login_ident or not login_pass:
                    st.error("Please enter both your Mail ID / Username and Password.")
                else:
                    with st.spinner("Authenticating with MongoDB Atlas..."):
                        ok, msg, user_obj = user_service.login(login_ident, login_pass)
                    if ok and user_obj:
                        st.session_state["user"] = user_obj
                        st.session_state["current_page"] = "Home"
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

            st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
            with st.expander("💡 Quick Demo / Test Sign-In"):
                st.caption("You can use this verified test account or create your own:")
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    if st.button("Load Test Account", key="btn_fill_demo_user", use_container_width=True):
                        ok, msg, user_obj = user_service.login("test_shreeyansh@gmail.com", "mypassword123")
                        if ok and user_obj:
                            st.session_state["user"] = user_obj
                            st.session_state["current_page"] = "Home"
                            st.rerun()
                with col_d2:
                    st.write("`test_shreeyansh@gmail.com`")

        # ── TAB 2: SIGN UP (CREATE ACCOUNT) ──
        with tab_signup:
            st.markdown("<div style='padding-top: 0.5rem;'></div>", unsafe_allow_html=True)
            st.caption("Your Mail ID and password will be securely hashed and stored in MongoDB Atlas.")

            reg_email = st.text_input(
                "Mail ID *",
                key="portal_reg_email",
                placeholder="e.g. yourname@example.com"
            )
            reg_username = st.text_input(
                "Display Name / Username (Optional)",
                key="portal_reg_uname",
                placeholder="Leave blank to use email handle"
            )
            reg_pass = st.text_input(
                "Create Password *",
                type="password",
                key="portal_reg_pass",
                placeholder="At least 4 characters"
            )
            reg_pass2 = st.text_input(
                "Confirm Password *",
                type="password",
                key="portal_reg_pass2",
                placeholder="Re-enter your password"
            )

            st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
            if st.button("✨ Create Account & Store in MongoDB", type="primary", use_container_width=True, key="portal_btn_signup"):
                if not reg_email or not reg_pass:
                    st.error("Mail ID and Password are required.")
                elif reg_pass != reg_pass2:
                    st.error("Passwords do not match. Please re-enter carefully.")
                elif len(reg_pass) < 4:
                    st.error("Password must be at least 4 characters long.")
                else:
                    with st.spinner("Registering user in MongoDB Atlas..."):
                        ok, msg, user_obj = user_service.register(
                            email=reg_email,
                            password=reg_pass,
                            username=reg_username
                        )
                    if ok and user_obj:
                        st.session_state["user"] = user_obj
                        st.session_state["current_page"] = "Home"
                        st.success(msg)
                        st.toast("Account created successfully! Welcome to MovieMind.", icon="🎉")
                        st.rerun()
                    else:
                        st.error(msg)

        # Feature highlights below card
        st.markdown("""
        <div style="margin-top: 2rem;">
            <div class="auth-pill-feature">
                <span>🍿</span>
                <span><strong>Personalized My List:</strong> Saves your watchlist directly to MongoDB Atlas.</span>
            </div>
            <div class="auth-pill-feature">
                <span>⚡</span>
                <span><strong>Evaluated Recommendations:</strong> Content + Collaborative Filtering tuned to your list.</span>
            </div>
            <div class="auth-pill-feature">
                <span>📊</span>
                <span><strong>Visual Analytics:</strong> Bar Graph, Pie Chart, and Box Plot tailored to your taste.</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
