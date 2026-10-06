import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import json
from config.config import MODELS_DIR, ALS_PARAMS
from app.services.recommender import recommender_service
from app.services.movies import catalog_service

def render_analytics():
    """Renders the Big Data System Analytics dashboard for academic evaluations, viva, and demonstrations."""
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <span style="background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.3); color: #38bdf8; padding: 0.35rem 0.85rem; border-radius: 9999px; font-size: 0.82rem; font-weight: 600; text-transform: uppercase;">
            Distributed Systems & Machine Learning Audit
        </span>
        <h1 style="font-size: 2.5rem; font-weight: 800; margin: 0.5rem 0 0.2rem 0;">📊 Big Data System Analytics</h1>
        <p style="color: #94a3b8; font-size: 1rem;">
            Comparative benchmarking of the Apache Spark ALS distributed pipeline and current deployment metrics.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Load active model metrics from JSON
    metrics_file = MODELS_DIR / "model_metrics.json"
    active_metrics = {}
    if metrics_file.exists():
        try:
            with open(metrics_file, "r", encoding="utf-8") as f:
                active_metrics = json.load(f)
        except Exception:
            pass

    # 1. Headline Metrics Grid
    st.markdown("<h3 style='font-size: 1.3rem; color: #fff;'>⚡ Spark MLlib Pipeline Performance</h3>", unsafe_allow_html=True)
    
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

    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)

    # 2. Side-by-Side Comparison: Academic Big Data Cluster vs Active Instance
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
        | **Unique Movies** | **23,350** | **3,650 (filtered >= 5)** |
        | **Train Split (80%)**| **25,379,611** rows | **72,120** rows |
        | **Test Split (20%)** | **6,346,309** rows | **18,154** rows |
        | **Training Duration**| **258.71 seconds (< 5 min)** | **8.51 seconds** |
        | **Evaluation RMSE** | **0.8104** | **0.8540** |
        """)

    with col_params:
        st.markdown("<h3 style='font-size: 1.2rem; color: #fff;'>⚙️ Spark ALS Hyperparameters</h3>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="glass-box">
            <div style="font-family: monospace; font-size: 0.88rem; color: #cbd5e1; line-height: 1.8;">
                <div><strong style="color: #e11d48;">maxIter:</strong> {ALS_PARAMS['maxIter']}</div>
                <div><strong style="color: #e11d48;">regParam:</strong> {ALS_PARAMS['regParam']}</div>
                <div><strong style="color: #e11d48;">userCol:</strong> "{ALS_PARAMS['userCol']}"</div>
                <div><strong style="color: #e11d48;">itemCol:</strong> "{ALS_PARAMS['itemCol']}"</div>
                <div><strong style="color: #e11d48;">ratingCol:</strong> "{ALS_PARAMS['ratingCol']}"</div>
                <div><strong style="color: #e11d48;">coldStartStrategy:</strong> "{ALS_PARAMS['coldStartStrategy']}"</div>
                <div><strong style="color: #e11d48;">nonnegative:</strong> {ALS_PARAMS['nonnegative']}</div>
                <div><strong style="color: #e11d48;">seed:</strong> {ALS_PARAMS['seed']}</div>
            </div>
            <hr style="margin: 0.8rem 0; border: none; border-bottom: 1px solid rgba(255,255,255,0.08);">
            <div style="font-size: 0.78rem; color: #94a3b8;">
                Hyperparameters strictly preserved from <code>SparkNotebook.ipynb</code> to honor collaborative filtering formulation.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 3. System Architecture Diagram
    st.markdown("<h3 style='font-size: 1.3rem; color: #fff; margin-top: 1.5rem;'>🏗️ End-to-End Pipeline Architecture</h3>", unsafe_allow_html=True)
    st.markdown("""
    ```
    ┌───────────────────────────┐
    │     MovieLens Dataset     │  (movies.csv, ratings.csv, links.csv)
    └─────────────┬─────────────┘
                  │ Ingestion
                  ▼
    ┌───────────────────────────┐
    │  Hadoop HDFS Storage      │  (hdfs://namenode:9000/user/rawan/movielens/)
    └─────────────┬─────────────┘
                  │ Distributed Read
                  ▼
    ┌───────────────────────────┐
    │  Apache Spark Cluster     │  (Driver 4G / Executor 4G / PySpark SQL)
    └─────────────┬─────────────┘
                  │ Preprocessing: User & Item Filtering (count >= 20)
                  ▼
    ┌───────────────────────────┐
    │  Spark MLlib ALS Engine   │  (Alternating Least Squares, regParam=0.1, maxIter=10)
    └─────────────┬─────────────┘
                  │ Model Evaluation & Recommendation Serialization
                  ▼
    ┌───────────────────────────┐
    │  Recommendation Service   │  (ALS Latent Vectors + Content Cosine Similarity)
    └─────────────┬─────────────┘
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
    ┌─────────────┐   ┌─────────────┐
    │ TMDb API    │   │ SQLite DB   │
    │ (Posters,   │   │ (Users,     │
    │  Backdrops, │   │  Watchlist, │
    │  Trailers)  │   │  Ratings)   │
    └──────┬──────┘   └──────┬──────┘
           │                 │
           └────────┬────────┘
                    ▼
    ┌───────────────────────────┐
    │ Streamlit Web Application │  (Responsive Cinematic Interface)
    └───────────────────────────┘
    ```
    """)

    # 4. Live Recommendation Tester for Viva / Demonstration
    st.markdown("<h3 style='font-size: 1.3rem; color: #fff; margin-top: 2rem;'>🔬 Live ALS Recommendation Inspector</h3>", unsafe_allow_html=True)
    st.caption("Inspect raw mathematical recommendations directly produced by the Spark ALS model:")

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
    import sys
    from pathlib import Path
    ROOT_DIR = Path(__file__).resolve().parent.parent.parent
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))
    import streamlit as st
    st.set_page_config(page_title="MovieMind | System Analytics", page_icon="🎬", layout="wide", initial_sidebar_state="expanded")
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
    render_analytics()
