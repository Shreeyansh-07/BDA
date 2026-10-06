# Implementation Specification & Repository Audit

## 1. Existing Repository Audit

After a thorough inspection of all files in the repository:
- **`README.md`**: Outlines a big data recommendation system using Apache Spark (MLlib), Hadoop HDFS, and Streamlit, referencing `app/`, `data/`, `models/`, `requirements.txt`, and training scripts. However, none of these directories or files existed in the repository prior to this implementation.
- **`Notebook.ipynb`**: Baseline exploratory notebook using pandas, scikit-learn, and the `implicit` ALS library.
  - Read from local paths: `C:\Users\fadwa\Downloads\ml-32m\ml-32m\movies.csv`, `ratings.csv`, `tags.csv`, `links.csv`.
  - Filtered users (>= 20 ratings) and movies (>= 20 ratings).
  - Train/test split (80/20) with random seed 42.
  - Achieved RMSE ≈ 3.68 using `implicit.als.AlternatingLeastSquares(factors=50, regularization=0.1, iterations=20)`.
  - Contained user recommendation logic, genre-based recommendations, and ratings distributions.
- **`SparkNotebook.ipynb`**: The primary distributed big data pipeline using PySpark MLlib.
  - HDFS Data paths: `hdfs://namenode:9000/user/rawan/movielens/movies.csv` and `ratings.csv`.
  - Spark Configuration:
    - Master: `spark://spark-master:7077`
    - Driver Memory: `4g`
    - Executor Memory: `4g`
    - Hadoop FS: `hdfs://namenode:9000`
  - Data Preprocessing:
    - Filtered users with `count(rating) >= 20`
    - Filtered movies with `count(rating) >= 20`
    - Mean-centering (`rating_centered = rating - rating_avg`)
    - 80/20 train/test split (seed 42)
    - Dataset scale: 31,725,920 ratings, 200,948 users, 23,350 movies.
  - Spark MLlib ALS Configuration:
    ```python
    ALS(
        maxIter=10,
        regParam=0.1,
        userCol="userId",
        itemCol="movieId",
        ratingCol="rating",
        coldStartStrategy="drop",
        nonnegative=True,
        seed=42
    )
    ```
  - Achieved test RMSE: **0.8104**.
  - Benchmarked execution time: 278.18s total (Training: 258.71s, Prediction: 0.05s, Preprocessing: 0.09s, Loading: 19.33s).
  - Top-N recommendations for user subsets (`model.recommendForUserSubset`).

### Missing Components Identified in Initial Repo:
1. No `app/` folder or Streamlit UI code.
2. No standalone PySpark training or recommendation scripts (`train_model.py`, `generate_recommendations.py`).
3. No dataset included in the repository (MovieLens files `movies.csv`, `ratings.csv`, `links.csv`).
4. No TMDb API integration or metadata service.
5. No user authentication, rating persistence, or watchlist database.
6. No environment configuration (`.env.example`) or Docker orchestration files.
7. No R script for academic demonstrations where Hadoop and R / SparkR are examined.

---

## 2. Target Architecture

```
MovieLens Dataset (movies.csv, ratings.csv, links.csv)
                      │
                      ▼
               Hadoop HDFS (hdfs://namenode:9000)
                      │
                      ▼
        Apache Spark Distributed Engine (PySpark / SparkR)
                      │
      ┌───────────────┴───────────────┐
      │ Data Preprocessing & Cleaning │ (Users >= 20, Movies >= 20)
      │ Rating Normalization & Split  │ (80/20 Split, Seed 42)
      └───────────────┬───────────────┘
                      │
                      ▼
          Spark MLlib ALS Recommendation Engine
       (maxIter=10, regParam=0.1, nonnegative=True)
                      │
                      ▼
        Trained Model & Precomputed Recommendations
                      │
                      ▼
             Recommendation Service
       (ALS Engine + Content Similarity + Cold Start Fallbacks)
                      │
         ┌────────────┴────────────┐
         ▼                         ▼
   TMDb API Service          SQLite Database
  (Metadata, Posters,       (Users, Watchlist,
   Backdrops, Trailers)      New Ratings)
         │                         │
         └────────────┬────────────┘
                      ▼
             Streamlit Application
    (Cinematic UI, Search, Details, System Analytics)
```

---

## 3. Directory Layout Constructed

- `spark/`
  - `SparkNotebook.ipynb` (Preserved)
  - `Notebook.ipynb` (Preserved)
  - `train_model.py` (Distributed / standalone PySpark training pipeline)
  - `generate_recommendations.py` (Batch top-N recommendation generation)
  - `recommendation_hadoop_r.R` (Hadoop / SparkR / R analysis script)
- `data/`
  - Curated MovieLens dataset with `movies.csv`, `ratings.csv`, `links.csv`
- `models/`
  - `als_model/` and precomputed ALS recommendation indices
- `app/`
  - `streamlit_app.py` (Main entry point with navigation and cinematic theme)
  - `pages/` (Home, Search, Movie Details, Recommendations, Watchlist, Profile, Analytics)
  - `components/` (Movie Card, Movie Row, Navbar, Sidebar)
  - `services/` (Recommender, TMDb API, Movies catalog, Users & Auth)
  - `utils/` (Cache, Helpers)
  - `assets/` (Custom CSS with dark glassmorphism, cinematic typography)
- `config/`
  - `config.py` (Environment variables and system paths)
- `Dockerfile` & `docker-compose.yml`
- `.env.example`
- `requirements.txt`
