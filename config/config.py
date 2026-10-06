import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if present
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# TMDB Configuration
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "4e44d9029b1270a757cddc766a1bcb63")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p"
TMDB_POSTER_SIZE = "w500"
TMDB_BACKDROP_SIZE = "w1280"

# Big Data (Spark & Hadoop HDFS) Configuration
SPARK_MASTER = os.getenv("SPARK_MASTER", "local[*]")
HDFS_NAMENODE = os.getenv("HDFS_NAMENODE", "hdfs://namenode:9000")
HDFS_DATA_PATH = os.getenv("HDFS_DATA_PATH", f"{HDFS_NAMENODE}/user/rawan/movielens")

# Storage Paths
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
MODELS_DIR = Path(os.getenv("MODELS_DIR", BASE_DIR / "models"))
DB_PATH = Path(os.getenv("DATABASE_PATH", DATA_DIR / "app_database.db"))

# MongoDB Database Configuration
MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://keshavsingh10008:Shreeyansh%4027@cluster0.akqenop.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "moviemind")

# ALS Hyperparameters (Preserved from SparkNotebook.ipynb)
ALS_PARAMS = {
    "maxIter": int(os.getenv("ALS_MAX_ITER", 10)),
    "regParam": float(os.getenv("ALS_REG_PARAM", 0.1)),
    "userCol": "userId",
    "itemCol": "movieId",
    "ratingCol": "rating",
    "coldStartStrategy": "drop",
    "nonnegative": True,
    "seed": 42
}

# Cache configurations
CACHE_TTL = 3600  # 1 hour
