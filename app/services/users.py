import sqlite3
import hashlib
import os
import time
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from config.config import DB_PATH, DATA_DIR

def init_db():
    """Initializes SQLite database tables for users, ratings, and watchlists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # User Ratings Table (New ratings submitted via Web UI)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            userId INTEGER NOT NULL,
            movieId INTEGER NOT NULL,
            rating REAL NOT NULL,
            timestamp INTEGER NOT NULL,
            PRIMARY KEY (userId, movieId)
        )
    """)

    # User Watchlist Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            userId INTEGER NOT NULL,
            movieId INTEGER NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (userId, movieId)
        )
    """)

    conn.commit()
    conn.close()

# Initialize DB on load
init_db()

def _hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """Hashes password securely using SHA-256 and cryptographic salt."""
    if salt is None:
        salt = os.urandom(16).hex()
    hashed = hashlib.sha256((salt + password).encode('utf-8')).hexdigest()
    return hashed, salt

def _verify_password(password: str, stored_hash: str, salt: str) -> bool:
    hashed, _ = _hash_password(password, salt)
    return hashed == stored_hash

class UserService:
    @staticmethod
    def register(username: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        username = username.strip()
        if not username or len(username) < 3:
            return False, "Username must be at least 3 characters long.", None
        if not password or len(password) < 4:
            return False, "Password must be at least 4 characters long.", None

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            hashed, salt = _hash_password(password)
            cursor.execute(
                "INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
                (username, hashed, salt)
            )
            conn.commit()
            user_id = cursor.lastrowid
            user = {
                "id": user_id,
                "username": username,
                "created_at": datetime.now().isoformat()
            }
            return True, "Registration successful!", user
        except sqlite3.IntegrityError:
            return False, "Username already exists. Please choose another.", None
        finally:
            conn.close()

    @staticmethod
    def login(username: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        username = username.strip()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT id, username, password_hash, salt, created_at FROM users WHERE username = ?",
                (username,)
            )
            row = cursor.fetchone()
            if not row:
                return False, "Invalid username or password.", None

            user_id, uname, stored_hash, salt, created_at = row
            if _verify_password(password, stored_hash, salt):
                user = {
                    "id": user_id,
                    "username": uname,
                    "created_at": created_at
                }
                return True, "Login successful!", user
            else:
                return False, "Invalid username or password.", None
        finally:
            conn.close()

    @staticmethod
    def add_to_watchlist(user_id: int, movie_id: int) -> bool:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO watchlist (userId, movieId) VALUES (?, ?)",
                (user_id, movie_id)
            )
            conn.commit()
            return True
        finally:
            conn.close()

    @staticmethod
    def remove_from_watchlist(user_id: int, movie_id: int) -> bool:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM watchlist WHERE userId = ? AND movieId = ?",
                (user_id, movie_id)
            )
            conn.commit()
            return True
        finally:
            conn.close()

    @staticmethod
    def is_in_watchlist(user_id: int, movie_id: int) -> bool:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT 1 FROM watchlist WHERE userId = ? AND movieId = ?",
                (user_id, movie_id)
            )
            return cursor.fetchone() is not None
        finally:
            conn.close()

    @staticmethod
    def get_watchlist(user_id: int) -> List[int]:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT movieId FROM watchlist WHERE userId = ? ORDER BY added_at DESC",
                (user_id,)
            )
            rows = cursor.fetchall()
            return [r[0] for r in rows]
        finally:
            conn.close()

    @staticmethod
    def rate_movie(user_id: int, movie_id: int, rating: float) -> bool:
        """Stores user ratings for movies (1.0 to 5.0)."""
        ts = int(time.time())
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO ratings (userId, movieId, rating, timestamp)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(userId, movieId) DO UPDATE SET rating=excluded.rating, timestamp=excluded.timestamp
                """,
                (user_id, movie_id, rating, ts)
            )
            conn.commit()
            return True
        finally:
            conn.close()

    @staticmethod
    def get_user_rating(user_id: int, movie_id: int) -> Optional[float]:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT rating FROM ratings WHERE userId = ? AND movieId = ?",
                (user_id, movie_id)
            )
            row = cursor.fetchone()
            return row[0] if row else None
        finally:
            conn.close()

    @staticmethod
    def get_user_rated_movies(user_id: int) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT movieId, rating, timestamp FROM ratings WHERE userId = ? ORDER BY timestamp DESC",
                (user_id,)
            )
            rows = cursor.fetchall()
            return [{"movieId": r[0], "rating": r[1], "timestamp": r[2]} for r in rows]
        finally:
            conn.close()

user_service = UserService()
