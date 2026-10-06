"""
Apache Spark MLlib ALS Recommendation Model Training Pipeline
Extracted and standardized from SparkNotebook.ipynb.

This script executes:
1. Distributed connection to Apache Spark and Hadoop HDFS.
2. Ingestion of MovieLens datasets (ratings.csv, movies.csv).
3. Big Data preprocessing: NA removal, user/movie interaction filtering (count >= 20).
4. User mean-centering normalization.
5. 80/20 Train/Test split with seed 42.
6. ALS Collaborative Filtering training:
   - maxIter = 10
   - regParam = 0.1
   - coldStartStrategy = 'drop'
   - nonnegative = True
   - seed = 42
7. Evaluation using RegressionEvaluator (RMSE).
8. Model export and recommendation matrix pre-generation.
"""

import os
import sys
import time
import json
from pathlib import Path

# Fix Windows console UTF-8 printing
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.config import (
    SPARK_MASTER,
    HDFS_NAMENODE,
    HDFS_DATA_PATH,
    DATA_DIR,
    MODELS_DIR,
    ALS_PARAMS
)

def get_spark_session(use_hdfs=False):
    """Initializes and returns an Apache Spark session configured for HDFS and ALS."""
    from pyspark.sql import SparkSession
    print(f"[*] Initializing Spark Session with Master: {SPARK_MASTER}...")
    builder = SparkSession.builder \
        .appName("MovieLens_ALS_Training") \
        .master(SPARK_MASTER) \
        .config("spark.driver.memory", "4g") \
        .config("spark.executor.memory", "4g") \
        .config("spark.sql.shuffle.partitions", "50")

    # If running with a remote HDFS namenode in cluster
    if use_hdfs and HDFS_NAMENODE and "hdfs://" in HDFS_NAMENODE:
        builder = builder.config("spark.hadoop.fs.defaultFS", HDFS_NAMENODE)

    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    return spark

def resolve_data_paths():
    """
    Resolves data locations, testing if HDFS namenode is accessible,
    otherwise cleanly falling back to local files.
    """
    hdfs_ratings = f"{HDFS_DATA_PATH}/ratings.csv"
    hdfs_movies = f"{HDFS_DATA_PATH}/movies.csv"
    
    local_ratings = str(DATA_DIR / "ratings.csv").replace("\\", "/")
    local_movies = str(DATA_DIR / "movies.csv").replace("\\", "/")

    # Check if HDFS namenode host can be resolved
    import socket
    hdfs_reachable = False
    if HDFS_NAMENODE and "hdfs://" in HDFS_NAMENODE:
        try:
            parts = HDFS_NAMENODE.replace("hdfs://", "").split(":")
            host = parts[0]
            port = int(parts[1]) if len(parts) > 1 else 9000
            s = socket.create_connection((host, port), timeout=2)
            s.close()
            hdfs_reachable = True
            print(f"[+] Successfully reached Hadoop HDFS NameNode at {HDFS_NAMENODE}")
        except Exception:
            hdfs_reachable = False
            print(f"[-] HDFS NameNode at {HDFS_NAMENODE} not reachable locally. Using local dataset.")

    if hdfs_reachable:
        return hdfs_ratings, hdfs_movies, True

    if not (DATA_DIR / "ratings.csv").exists():
        raise FileNotFoundError(f"Ratings dataset not found at {local_ratings} or on HDFS.")

    print(f"[+] Using local dataset at {local_ratings}")
    return local_ratings, local_movies, False

def train_and_evaluate(spark, ratings_path, movies_path):
    from pyspark.sql.functions import col, count, avg
    from pyspark.sql.types import IntegerType, FloatType
    from pyspark.ml.recommendation import ALS
    from pyspark.ml.evaluation import RegressionEvaluator

    timings = {}

    # 1. Ingestion
    t0 = time.time()
    print("[*] Ingesting datasets...")
    movies_df = spark.read.csv(movies_path, header=True, inferSchema=True)
    ratings_df = spark.read.csv(ratings_path, header=True, inferSchema=True)
    timings["data_load_time"] = round(time.time() - t0, 2)
    print(f"[✓] Data loaded in {timings['data_load_time']}s")

    raw_ratings_count = ratings_df.count()
    raw_users_count = ratings_df.select("userId").distinct().count()
    raw_movies_count = ratings_df.select("movieId").distinct().count()
    print(f"    Raw Ratings: {raw_ratings_count:,} | Users: {raw_users_count:,} | Movies: {raw_movies_count:,}")

    # 2. Cleaning & Preprocessing (identical to SparkNotebook.ipynb)
    t0 = time.time()
    ratings_df = ratings_df.dropna()

    # Determine interactive threshold (20 for full dataset, or adaptive min for smaller sets)
    min_interactions = 20 if raw_ratings_count > 500000 else 5
    user_counts = ratings_df.groupBy("userId").agg(count("rating").alias("rating_count")).filter(col("rating_count") >= min_interactions)
    movie_counts = ratings_df.groupBy("movieId").agg(count("rating").alias("rating_count")).filter(col("rating_count") >= min_interactions)

    ratings_df = ratings_df.join(user_counts, "userId", "inner").select(ratings_df["*"])
    ratings_df = ratings_df.join(movie_counts, "movieId", "inner").select(ratings_df["*"])

    # Cast IDs for ALS
    ratings_df = ratings_df.withColumn("userId", col("userId").cast(IntegerType())) \
                           .withColumn("movieId", col("movieId").cast(IntegerType())) \
                           .withColumn("rating", col("rating").cast(FloatType()))

    # Rating centering (computed for tracking and analysis)
    user_avg = ratings_df.groupBy("userId").agg(avg("rating").alias("rating_avg"))
    ratings_df = ratings_df.join(user_avg, "userId")
    ratings_df = ratings_df.withColumn("rating_centered", col("rating") - col("rating_avg"))

    cleaned_ratings_count = ratings_df.count()
    cleaned_users_count = ratings_df.select("userId").distinct().count()
    cleaned_movies_count = ratings_df.select("movieId").distinct().count()
    timings["preprocessing_time"] = round(time.time() - t0, 2)
    print(f"[✓] Preprocessing completed in {timings['preprocessing_time']}s")
    print(f"    Cleaned Ratings: {cleaned_ratings_count:,} | Users: {cleaned_users_count:,} | Movies: {cleaned_movies_count:,}")

    # 3. Train / Test Split (80/20, seed 42)
    train_df, test_df = ratings_df.randomSplit([0.8, 0.2], seed=42)
    train_count = train_df.count()
    test_count = test_df.count()
    print(f"    Train Split: {train_count:,} | Test Split: {test_count:,}")

    # 4. Train Spark MLlib ALS
    t0 = time.time()
    print(f"[*] Training Spark MLlib ALS with parameters: {ALS_PARAMS}...")
    als = ALS(
        maxIter=ALS_PARAMS["maxIter"],
        regParam=ALS_PARAMS["regParam"],
        userCol=ALS_PARAMS["userCol"],
        itemCol=ALS_PARAMS["itemCol"],
        ratingCol=ALS_PARAMS["ratingCol"],
        coldStartStrategy=ALS_PARAMS["coldStartStrategy"],
        nonnegative=ALS_PARAMS["nonnegative"],
        seed=ALS_PARAMS["seed"]
    )
    model = als.fit(train_df)
    timings["training_time"] = round(time.time() - t0, 2)
    print(f"[✓] Model trained in {timings['training_time']}s")

    # 5. Evaluate Test RMSE
    t0 = time.time()
    predictions = model.transform(test_df)
    evaluator = RegressionEvaluator(metricName="rmse", labelCol="rating", predictionCol="prediction")
    rmse = evaluator.evaluate(predictions)
    timings["prediction_time"] = round(time.time() - t0, 2)
    timings["total_time"] = round(sum(timings.values()), 2)
    print(f"[✓] Evaluation completed in {timings['prediction_time']}s")
    print(f"[★] Test RMSE: {rmse:.4f}")

    # 6. Save Model to models/als_model
    model_save_path = str(MODELS_DIR / "als_model")
    print(f"[*] Saving trained ALS model to {model_save_path}...")
    try:
        model.write().overwrite().save(model_save_path)
        print("[✓] ALS model successfully saved.")
    except Exception as e:
        print(f"[-] Warning: Failed to save Spark ML model: {e}")

    # 7. Generate & Export Top Recommendations for Fast UI Serving
    print("[*] Pre-generating Top-20 recommendations for active users...")
    try:
        recs = model.recommendForAllUsers(20)
        recs_pd = recs.toPandas()
        
        # Serialize recommendations to JSON dictionary: {userId: [[movieId, predRating], ...]}
        rec_dict = {}
        for _, row in recs_pd.iterrows():
            u_id = int(row["userId"])
            items = [[int(r["movieId"]), round(float(r["rating"]), 2)] for r in row["recommendations"]]
            rec_dict[u_id] = items

        rec_file = MODELS_DIR / "als_recommendations.json"
        with open(rec_file, "w", encoding="utf-8") as f:
            json.dump(rec_dict, f)
        print(f"[✓] Saved {len(rec_dict)} user recommendation profiles to {rec_file}")
    except Exception as e:
        print(f"[-] Warning generating batch recommendations: {e}")

    # 8. Save Metrics Artifact for System Analytics Page
    metrics = {
        "raw_ratings": raw_ratings_count,
        "raw_users": raw_users_count,
        "raw_movies": raw_movies_count,
        "cleaned_ratings": cleaned_ratings_count,
        "unique_users": cleaned_users_count,
        "unique_movies": cleaned_movies_count,
        "train_set_size": train_count,
        "test_set_size": test_count,
        "als_params": ALS_PARAMS,
        "rmse": round(rmse, 4),
        "execution_timings": timings,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    metrics_file = MODELS_DIR / "model_metrics.json"
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(f"[✓] Saved model analytics to {metrics_file}")

    return model, rmse, metrics

def main():
    print("=" * 70)
    print("🎬 MovieLens Spark ALS Training Pipeline")
    print("=" * 70)
    ratings_path, movies_path, use_hdfs = resolve_data_paths()
    spark = get_spark_session(use_hdfs=use_hdfs)
    train_and_evaluate(spark, ratings_path, movies_path)
    spark.stop()
    print("=" * 70)
    print("🎉 Pipeline Execution Finished Successfully!")
    print("=" * 70)

if __name__ == "__main__":
    main()
