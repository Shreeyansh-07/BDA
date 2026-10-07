import sys
from pathlib import Path
from typing import Dict, Any, List

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import json
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from config.config import MODELS_DIR, ALS_PARAMS
from app.services.recommender import recommender_service
from app.services.movies import catalog_service
from app.services.users import user_service

# Cinematic Color Palette
CINEMATIC_COLORS = [
    "#e50914", "#f59e0b", "#10b981", "#06b6d4",
    "#8b5cf6", "#ec4899", "#3b82f6", "#14b8a6",
    "#f97316", "#84cc16"
]

def render_analytics():
    """
    Renders personalized analytics for the active user:
    - Bar Graph: Personalized recommendation match scores & genre counts
    - Pie Chart: Personalized taste & genre breakdown
    - Box Plot: Statistical distribution of predicted ratings across genres
    Plus Distributed Apache Spark ALS benchmarks.
    """
    user = st.session_state.get("user")
    if not user:
        from app.components.auth_portal import render_auth_portal
        render_auth_portal()
        return

    user_id = user.get("id", 1)
    username = user.get("username", f"User {user_id}")
    email = user.get("email")

    # Header
    st.markdown(f"""
    <div style="margin-bottom: 1.5rem;">
        <span style="background: rgba(229, 9, 20, 0.15); border: 1px solid rgba(229, 9, 20, 0.3); color: #ff4d4d; padding: 0.35rem 0.85rem; border-radius: 9999px; font-size: 0.82rem; font-weight: 700; text-transform: uppercase;">
            Personalized Analytics & Big Data Audit
        </span>
        <h1 style="font-size: 2.4rem; font-weight: 900; margin: 0.5rem 0 0.2rem 0; color: #fff;">
            📊 Recommendation Analytics
        </h1>
        <p style="color: #94a3b8; font-size: 0.95rem;">
            Dynamic visual analytics tailored specifically for <strong>{username}</strong> based on your Watchlist (My List) and ALS collaborative filtering.
        </p>
    </div>
    """, unsafe_allow_html=True)

    tab_user, tab_system = st.tabs([
        "🎯 Personalized User Analytics",
        "⚡ Distributed Spark ALS Pipeline"
    ])

    with tab_user:
        _render_user_personalized_analytics(user_id, username, email)

    with tab_system:
        _render_system_pipeline_analytics()

def _render_user_personalized_analytics(user_id: Any, username: str, email: str = None):
    """Renders the Bar Graph, Pie Chart, and Box Plot for user recommendations."""
    # 1. Fetch user taste and recommendations
    taste_profile = recommender_service.get_user_taste_profile(user_id, email=email)
    watchlist_eval = recommender_service.evaluate_watchlist(user_id, email=email)
    recs = taste_profile["recommendations"]

    watchlist_count = taste_profile["watchlist_count"]
    rated_count = taste_profile["rated_count"]

    # Notification banner if user has an empty watchlist
    if watchlist_count == 0:
        st.markdown("""
        <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.25); border-radius: 8px; padding: 0.85rem 1.25rem; margin-bottom: 1.5rem; display: flex; align-items: center; justify-content: space-between;">
            <div style="color: #fbbf24; font-size: 0.88rem;">
                💡 <strong>Watchlist is currently empty:</strong> Add movies to <em>My List</em> via "+ ADD LIST" on any title to customize your personalized recommendations and analytics!
            </div>
        </div>
        """, unsafe_allow_html=True)

    # User Summary Cards
    col_u1, col_u2, col_u3, col_u4 = st.columns(4)
    with col_u1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value" style="color: #fff;">{watchlist_count}</div>
            <div class="stat-label">Titles in My List</div>
        </div>
        """, unsafe_allow_html=True)
    with col_u2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value" style="color: #38bdf8;">{len(recs)}</div>
            <div class="stat-label">Personalized Recs</div>
        </div>
        """, unsafe_allow_html=True)
    with col_u3:
        avg_score = np.mean([r.get("predicted_rating", 4.0) for r in recs]) if recs else 4.0
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value" style="color: #f59e0b;">★ {avg_score:.2f}</div>
            <div class="stat-label">Avg Predicted Match</div>
        </div>
        """, unsafe_allow_html=True)
    with col_u4:
        top_genre = taste_profile["top_genres"][0] if taste_profile["top_genres"] else "All Genres"
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value" style="color: #10b981;">{top_genre}</div>
            <div class="stat-label">Top Affinity Genre</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # Build DataFrame for personalized recommendations
    rec_records = []
    for r in recs:
        primary_genre = r.get("genres", ["Drama"])[0] if r.get("genres") else "Drama"
        for g in r.get("genres", ["Drama"]):
            rec_records.append({
                "movieId": r["movieId"],
                "title": r.get("title", f"Movie {r['movieId']}"),
                "year": r.get("year", "N/A"),
                "genre": g,
                "primary_genre": primary_genre,
                "predicted_rating": float(r.get("predicted_rating", 4.0)),
                "recommendation_source": r.get("recommendation_source", "ALS Engine"),
                "recommendation_reason": r.get("recommendation_reason", "Taste Match")
            })
    df_recs = pd.DataFrame(rec_records)

    # DataFrame of unique recommended titles
    unique_titles_data = []
    for r in recs:
        unique_titles_data.append({
            "movieId": r["movieId"],
            "title": r.get("title", f"Movie {r['movieId']}"),
            "primary_genre": r.get("genres", ["Drama"])[0] if r.get("genres") else "Drama",
            "predicted_rating": float(r.get("predicted_rating", 4.0)),
            "recommendation_source": r.get("recommendation_source", "ALS Engine"),
            "recommendation_reason": r.get("recommendation_reason", "Taste Match")
        })
    df_unique = pd.DataFrame(unique_titles_data)

    # ─────────────────────────────────────────────────────────────
    # 1. BAR GRAPH: Personalized Recommendations & Predicted Ratings
    # ─────────────────────────────────────────────────────────────
    st.markdown("<h3 style='font-size: 1.25rem; color: #fff; margin-bottom: 0.2rem;'>📊 1. Bar Graph: Personalized Recommendation Scores & Preferences</h3>", unsafe_allow_html=True)
    st.caption(f"Predicted affinity scores calculated specifically for {username} across top recommended titles.")

    col_bar_ctrl, _ = st.columns([4, 6])
    with col_bar_ctrl:
        bar_view = st.radio(
            "Bar Graph Dimension",
            options=["Top Recommended Movies (Predicted Score)", "Genre Frequency in Personal Feed"],
            horizontal=True,
            label_visibility="collapsed"
        )

    if not df_unique.empty:
        if bar_view == "Top Recommended Movies (Predicted Score)":
            top_bar_df = df_unique.sort_values(by="predicted_rating", ascending=True).tail(12)
            fig_bar = px.bar(
                top_bar_df,
                x="predicted_rating",
                y="title",
                orientation="h",
                color="primary_genre",
                color_discrete_sequence=CINEMATIC_COLORS,
                hover_data=["recommendation_reason", "recommendation_source"],
                labels={"predicted_rating": "Predicted Match Score (★)", "title": "Movie Title", "primary_genre": "Primary Genre"}
            )
            fig_bar.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(20,21,26,0.6)",
                font=dict(color="#cbd5e1", family="sans-serif"),
                xaxis=dict(gridcolor="rgba(255,255,255,0.06)", range=[3.0, 5.1]),
                yaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
                margin=dict(l=10, r=20, t=20, b=30),
                height=420,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            genre_freq_df = df_recs.groupby("genre").size().reset_index(name="count").sort_values(by="count", ascending=False)
            fig_bar_genre = px.bar(
                genre_freq_df,
                x="genre",
                y="count",
                color="genre",
                color_discrete_sequence=CINEMATIC_COLORS,
                labels={"genre": "Genre", "count": "Recommended Titles Count"}
            )
            fig_bar_genre.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(20,21,26,0.6)",
                font=dict(color="#cbd5e1", family="sans-serif"),
                xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
                margin=dict(l=10, r=20, t=20, b=30),
                height=380,
                showlegend=False
            )
            st.plotly_chart(fig_bar_genre, use_container_width=True)

    st.markdown("<hr style='margin: 1.8rem 0; border: none; border-bottom: 1px solid rgba(255,255,255,0.07);'>", unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────
    # 2. PIE CHART & 3. BOX PLOT (Side by Side Grid)
    # ─────────────────────────────────────────────────────────────
    col_pie, col_box = st.columns([5, 5])

    # ── PIE CHART ──
    with col_pie:
        st.markdown("<h3 style='font-size: 1.25rem; color: #fff; margin-bottom: 0.2rem;'>🥧 2. Pie Chart: Personalized Taste Breakdown</h3>", unsafe_allow_html=True)
        st.caption("Distribution of movie genres recommended based on your Watchlist and preferences.")

        if not df_recs.empty:
            genre_pie_data = df_recs.groupby("genre").size().reset_index(name="titles")
            fig_pie = px.pie(
                genre_pie_data,
                values="titles",
                names="genre",
                hole=0.45,
                color_discrete_sequence=CINEMATIC_COLORS
            )
            fig_pie.update_traces(
                textposition="inside",
                textinfo="percent+label",
                marker=dict(line=dict(color="#14151a", width=2))
            )
            fig_pie.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#cbd5e1", family="sans-serif"),
                margin=dict(l=10, r=10, t=20, b=20),
                height=380,
                showlegend=False
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No recommendations data to generate pie chart.")

    # ── BOX PLOT ──
    with col_box:
        st.markdown("<h3 style='font-size: 1.25rem; color: #fff; margin-bottom: 0.2rem;'>📦 3. Box Plot: Rating Distribution by Genre</h3>", unsafe_allow_html=True)
        st.caption("Statistical quartiles, median, and spread of predicted scores across recommended genres.")

        if not df_recs.empty:
            # Filter top 6 genres to keep box plot readable
            top_genre_names = df_recs["genre"].value_counts().head(6).index.tolist()
            filtered_box_df = df_recs[df_recs["genre"].isin(top_genre_names)]

            fig_box = px.box(
                filtered_box_df,
                x="genre",
                y="predicted_rating",
                color="genre",
                points="all",
                color_discrete_sequence=CINEMATIC_COLORS,
                labels={"genre": "Genre", "predicted_rating": "Predicted Score (★)"}
            )
            fig_box.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(20,21,26,0.6)",
                font=dict(color="#cbd5e1", family="sans-serif"),
                xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.04)", range=[3.2, 5.2]),
                margin=dict(l=10, r=10, t=20, b=20),
                height=380,
                showlegend=False
            )
            st.plotly_chart(fig_box, use_container_width=True)
        else:
            st.info("No data available for box plot.")

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # 4. Watchlist Evaluation Deep Dive
    with st.expander("🔍 Detailed Watchlist (My List) Evaluation Inspector"):
        st.markdown(f"#### Active Watchlist Items ({watchlist_count})")
        if watchlist_eval["watchlist_movies"]:
            wl_table_items = []
            for wm in watchlist_eval["watchlist_movies"]:
                wl_table_items.append({
                    "Movie ID": wm["movieId"],
                    "Title": wm["title"],
                    "Year": wm["year"],
                    "Genres": ", ".join(wm.get("genres", [])),
                    "Catalog Rating": f"{wm.get('avg_rating', 3.8):.1f} ★"
                })
            st.dataframe(pd.DataFrame(wl_table_items), use_container_width=True)
        else:
            st.write("No titles in My List yet. Browse films and click **+ ADD LIST** to add!")

def _render_system_pipeline_analytics():
    """Renders the distributed Apache Spark ALS pipeline benchmarking audit."""
    metrics_file = MODELS_DIR / "model_metrics.json"
    active_metrics = {}
    if metrics_file.exists():
        try:
            with open(metrics_file, "r", encoding="utf-8") as f:
                active_metrics = json.load(f)
        except Exception:
            pass

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-value" style="color: #38bdf8;">0.8104</div>
            <div class="stat-label">MovieLens 32M Test RMSE</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        current_rmse = active_metrics.get("rmse", 0.854)
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value" style="color: #34d399;">{current_rmse:.4f}</div>
            <div class="stat-label">Active Spark ALS RMSE</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-value">31.7M</div>
            <div class="stat-label">HDFS Cleaned Ratings</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-value">200,948</div>
            <div class="stat-label">Distributed Users Trained</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    col_bench, col_params = st.columns([6, 4])
    with col_bench:
        st.markdown("<h3 style='font-size: 1.2rem; color: #fff;'>📈 Dataset & Training Splits</h3>", unsafe_allow_html=True)
        st.markdown("""
        | Dimension | Hadoop HDFS + Spark Cluster (Notebook) | Active Local Deployment |
        | :--- | :--- | :--- |
        | **Dataset Source** | `hdfs://namenode:9000/user/rawan/movielens` | Local `data/ratings.csv` & `movies.csv` |
        | **Raw Ratings** | **32,000,000+** | **100,836** |
        | **Cleaned Ratings** | **31,725,920** | **90,274** |
        | **Unique Users** | **200,948** | **610** |
        | **Train Split (80%)**| **25,379,611** rows | **72,120** rows |
        | **Test Split (20%)** | **6,346,309** rows | **18,154** rows |
        | **Evaluation RMSE** | **0.8104** | **0.8540** |
        """)

    with col_params:
        st.markdown("<h3 style='font-size: 1.2rem; color: #fff;'>⚙️ Spark ALS Hyperparameters</h3>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="glass-box">
            <div style="font-family: monospace; font-size: 0.88rem; color: #cbd5e1; line-height: 1.8;">
                <div><strong style="color: #e50914;">maxIter:</strong> {ALS_PARAMS['maxIter']}</div>
                <div><strong style="color: #e50914;">regParam:</strong> {ALS_PARAMS['regParam']}</div>
                <div><strong style="color: #e50914;">userCol:</strong> "{ALS_PARAMS['userCol']}"</div>
                <div><strong style="color: #e50914;">itemCol:</strong> "{ALS_PARAMS['itemCol']}"</div>
                <div><strong style="color: #e50914;">ratingCol:</strong> "{ALS_PARAMS['ratingCol']}"</div>
                <div><strong style="color: #e50914;">coldStartStrategy:</strong> "{ALS_PARAMS['coldStartStrategy']}"</div>
                <div><strong style="color: #e50914;">nonnegative:</strong> {ALS_PARAMS['nonnegative']}</div>
                <div><strong style="color: #e50914;">seed:</strong> {ALS_PARAMS['seed']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Live Inspector
    st.markdown("<h3 style='font-size: 1.2rem; color: #fff; margin-top: 1.5rem;'>🔬 Live ALS Recommendation Inspector</h3>", unsafe_allow_html=True)
    test_user = st.number_input("Target User ID for Inspection", min_value=1, max_value=610, value=1, step=1)
    if st.button("Inspect User Recommendations", use_container_width=False):
        raw_recs = recommender_service.recommend_movies(user_id=test_user, n=5)
        st.markdown(f"#### Top 5 Spark ALS Recommendations for User {test_user}:")
        for rank, r in enumerate(raw_recs, 1):
            st.markdown(f"""
            - **Rank {rank}**: **{r['title']} ({r['year']})**  
              *MovieID*: `{r['movieId']}` | *ALS Score*: `{r.get('predicted_rating', 'N/A')} ★` | *Genres*: `{', '.join(r['genres'])}` | *Source*: `{r.get('recommendation_source')}`
            """)

if __name__ == "__main__":
    st.set_page_config(page_title="MovieMind | System Analytics", page_icon="🎬", layout="wide")
    render_analytics()
