"""
Batch and Targeted Top-N Recommendation Generation using Apache Spark ALS.
Standardized utility to generate recommendations for specific users or all users.
"""

import sys
import argparse
import json
from pathlib import Path

# Fix Windows console UTF-8 printing
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.config import MODELS_DIR, DATA_DIR, SPARK_MASTER

def generate_for_user(user_id: int, top_n: int = 10):
    """Loads recommendations from cached model matrix or Spark model."""
    rec_file = MODELS_DIR / "als_recommendations.json"
    if rec_file.exists():
        with open(rec_file, "r", encoding="utf-8") as f:
            all_recs = json.load(f)
        user_key = str(user_id)
        if user_key in all_recs:
            recs = all_recs[user_key][:top_n]
            print(f"\n[★] Top {len(recs)} ALS recommendations for User {user_id}:")
            for rank, (m_id, score) in enumerate(recs, 1):
                print(f"  {rank}. MovieID: {m_id:<6} | Predicted Rating: {score:.2f} ★")
            return recs
        else:
            print(f"[-] User {user_id} not found in precomputed ALS recommendations.")

    # Try loading from Spark ML model if available
    model_path = MODELS_DIR / "als_model"
    if model_path.exists():
        try:
            from pyspark.sql import SparkSession
            from pyspark.ml.recommendation import ALSModel
            spark = SparkSession.builder.appName("GenerateRecs").master("local[*]").getOrCreate()
            model = ALSModel.load(str(model_path))
            user_df = spark.createDataFrame([(user_id,)], ["userId"])
            user_recs = model.recommendForUserSubset(user_df, top_n).collect()
            if user_recs:
                recs = [(row.movieId, row.rating) for row in user_recs[0].recommendations]
                print(f"\n[★] Spark ALS recommendations for User {user_id}:")
                for rank, (m_id, score) in enumerate(recs, 1):
                    print(f"  {rank}. MovieID: {m_id:<6} | Predicted Rating: {score:.2f} ★")
                spark.stop()
                return recs
            spark.stop()
        except Exception as e:
            print(f"[-] Spark evaluation error: {e}")

    print("[-] No ALS recommendations available for this user.")
    return []

def main():
    parser = argparse.ArgumentParser(description="Generate Top-N Movie Recommendations using Apache Spark ALS.")
    parser.add_argument("--user", type=int, default=1, help="Target userId (default: 1)")
    parser.add_argument("--n", type=int, default=10, help="Number of recommendations (default: 10)")
    args = parser.parse_args()

    generate_for_user(args.user, args.n)

if __name__ == "__main__":
    main()
