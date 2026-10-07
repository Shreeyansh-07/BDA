import os
import re
import time
import hashlib
import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from config.config import DB_PATH, DATA_DIR, MONGODB_URI, MONGODB_DB_NAME

try:
    import certifi
    _ca_file = certifi.where()
except Exception:
    _ca_file = None

# Singleton Mongo client
_mongo_client: Optional[MongoClient] = None

def get_mongo_client() -> Optional[MongoClient]:
    """Returns a connected MongoClient singleton with certifi TLS, or None if connection fails."""
    global _mongo_client
    if _mongo_client is not None:
        try:
            # Quick ping check
            _mongo_client.admin.command("ping")
            return _mongo_client
        except Exception:
            _mongo_client = None

    try:
        kwargs = {
            "serverSelectionTimeoutMS": 10000,
            "connectTimeoutMS": 10000,
            "retryWrites": True,
        }
        if _ca_file:
            kwargs["tlsCAFile"] = _ca_file
        client = MongoClient(MONGODB_URI, **kwargs)
        client.admin.command("ping")
        _mongo_client = client
        return _mongo_client
    except Exception as e:
        print(f"[MongoDB Warning] Could not connect to Atlas cluster: {e}")
        return None

def get_mongo_db():
    """Returns the MongoDB database instance or None."""
    client = get_mongo_client()
    if client is not None:
        return client[MONGODB_DB_NAME]
    return None

def init_db():
    """Initializes SQLite database tables as fallback and initializes MongoDB indexes."""
    # 1. SQLite fallback initialization
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            userId INTEGER NOT NULL,
            movieId INTEGER NOT NULL,
            rating REAL NOT NULL,
            timestamp INTEGER NOT NULL,
            PRIMARY KEY (userId, movieId)
        )
    """)

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

    # 2. MongoDB indexes setup
    db = get_mongo_db()
    if db is not None:
        try:
            db.users.create_index([("email", 1)], unique=True)
            db.users.create_index([("username", 1)], unique=True)
            db.watchlist.create_index([("userId", 1), ("movieId", 1)], unique=True)
            db.ratings.create_index([("userId", 1), ("movieId", 1)], unique=True)
        except Exception as e:
            # If index exists with slightly different specs, ignore safely
            pass

# Initialize DB on load
init_db()

def _hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """Hashes password securely using SHA-256 and cryptographic salt."""
    if salt is None:
        salt = os.urandom(16).hex()
    hashed = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return hashed, salt

def _verify_password(password: str, stored_hash: str, salt: str) -> bool:
    hashed, _ = _hash_password(password, salt)
    return hashed == stored_hash

def _is_valid_email(email: str) -> bool:
    """Validates email format."""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email.strip()))

class UserService:
    @staticmethod
    def is_mongo_online() -> bool:
        """Returns True if MongoDB Atlas cluster is online and reachable."""
        return get_mongo_db() is not None

    @staticmethod
    def register(email: str, password: str, username: Optional[str] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Registers a new user with mail ID and password.
        Stores credentials securely in MongoDB (and syncs to local SQLite fallback).
        """
        email = email.strip().lower()
        if not email or not _is_valid_email(email):
            return False, "Please enter a valid email address (e.g. user@example.com).", None

        if not password or len(password) < 4:
            return False, "Password must be at least 4 characters long.", None

        if not username or not username.strip():
            username = email.split("@")[0]
        username = username.strip()

        hashed, salt = _hash_password(password)
        now_iso = datetime.utcnow().isoformat()

        # 1. Store in MongoDB
        db = get_mongo_db()
        if db is not None:
            try:
                # Check duplicate email
                if db.users.find_one({"email": email}):
                    return False, f"Account with email '{email}' already exists. Please sign in.", None
                
                # Check duplicate username
                if db.users.find_one({"username": username}):
                    # Make unique by adding random digits if collision
                    username = f"{username}_{os.urandom(2).hex()}"

                # Generate numeric user_id (MovieLens compatible)
                last_user = db.users.find_one(sort=[("user_id", -1)])
                next_id = (last_user.get("user_id", 1000) + 1) if (last_user and "user_id" in last_user) else 1001

                user_doc = {
                    "user_id": next_id,
                    "email": email,
                    "username": username,
                    "password_hash": hashed,
                    "salt": salt,
                    "created_at": now_iso,
                    "last_login": now_iso
                }
                res = db.users.insert_one(user_doc)

                user_obj = {
                    "id": next_id,
                    "email": email,
                    "username": username,
                    "created_at": now_iso,
                    "source": "MongoDB Atlas"
                }

                # Sync to SQLite fallback
                try:
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute(
                        "INSERT OR REPLACE INTO users (id, email, username, password_hash, salt, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                        (next_id, email, username, hashed, salt, now_iso)
                    )
                    conn.commit()
                    conn.close()
                except Exception:
                    pass

                return True, f"Registration successful! Welcome to MovieMind, {username}.", user_obj
            except Exception as e:
                return False, f"Database error during registration: {str(e)}", None

        # 2. SQLite Fallback if Mongo unreachable
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (email, username, password_hash, salt) VALUES (?, ?, ?, ?)",
                (email, username, hashed, salt)
            )
            conn.commit()
            user_id = cursor.lastrowid
            user_obj = {
                "id": user_id,
                "email": email,
                "username": username,
                "created_at": now_iso,
                "source": "Local SQLite"
            }
            return True, "Registration successful!", user_obj
        except sqlite3.IntegrityError:
            return False, "An account with this email or username already exists.", None
        finally:
            conn.close()

    @staticmethod
    def login(identifier: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Authenticates user using their Mail ID (or Username) and Password against MongoDB.
        """
        identifier = identifier.strip()
        if not identifier or not password:
            return False, "Please provide your email/username and password.", None

        # 1. Try MongoDB
        db = get_mongo_db()
        if db is not None:
            try:
                user_doc = db.users.find_one({
                    "$or": [
                        {"email": identifier.lower()},
                        {"username": identifier}
                    ]
                })

                if user_doc:
                    if _verify_password(password, user_doc["password_hash"], user_doc["salt"]):
                        # Update last login timestamp
                        db.users.update_one(
                            {"_id": user_doc["_id"]},
                            {"$set": {"last_login": datetime.utcnow().isoformat()}}
                        )
                        user_obj = {
                            "id": user_doc.get("user_id", 1),
                            "email": user_doc.get("email", identifier),
                            "username": user_doc.get("username", identifier),
                            "created_at": user_doc.get("created_at", datetime.utcnow().isoformat()),
                            "source": "MongoDB Atlas"
                        }
                        return True, f"Welcome back, {user_obj['username']}!", user_obj
                    else:
                        return False, "Incorrect password. Please try again.", None
            except Exception as e:
                print(f"[MongoDB Login Error] {e}")

        # 2. Fallback to SQLite
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT id, email, username, password_hash, salt, created_at FROM users WHERE email = ? OR username = ?",
                (identifier.lower(), identifier)
            )
            row = cursor.fetchone()
            if not row:
                return False, "No account found with this email or username.", None

            user_id, email, uname, stored_hash, salt, created_at = row
            if _verify_password(password, stored_hash, salt):
                user_obj = {
                    "id": user_id,
                    "email": email or identifier,
                    "username": uname,
                    "created_at": created_at,
                    "source": "Local SQLite"
                }
                return True, f"Welcome back, {uname}!", user_obj
            else:
                return False, "Incorrect password. Please try again.", None
        finally:
            conn.close()

    @staticmethod
    def add_to_watchlist(user_id: Any, movie_id: int, email: Optional[str] = None) -> bool:
        """Adds a movie to the user's Watchlist in MongoDB and SQLite."""
        movie_id = int(movie_id)
        now_dt = datetime.utcnow()

        db = get_mongo_db()
        if db is not None:
            try:
                db.watchlist.update_one(
                    {"userId": user_id, "movieId": movie_id},
                    {"$set": {
                        "userId": user_id,
                        "movieId": movie_id,
                        "email": email or "",
                        "added_at": now_dt
                    }},
                    upsert=True
                )
            except Exception as e:
                print(f"[Mongo Watchlist Add Error] {e}")

        # SQLite mirror
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            # If user_id is an integer, store directly
            numeric_uid = int(user_id) if isinstance(user_id, int) or (isinstance(user_id, str) and user_id.isdigit()) else 1
            c.execute(
                "INSERT OR IGNORE INTO watchlist (userId, movieId) VALUES (?, ?)",
                (numeric_uid, movie_id)
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

        return True

    @staticmethod
    def remove_from_watchlist(user_id: Any, movie_id: int, email: Optional[str] = None) -> bool:
        """Removes a movie from the user's Watchlist in MongoDB and SQLite."""
        movie_id = int(movie_id)

        db = get_mongo_db()
        if db is not None:
            try:
                query: Dict[str, Any] = {"movieId": movie_id}
                if email:
                    query["$or"] = [{"userId": user_id}, {"email": email}]
                else:
                    query["userId"] = user_id
                db.watchlist.delete_many(query)
            except Exception as e:
                print(f"[Mongo Watchlist Remove Error] {e}")

        # SQLite mirror
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            numeric_uid = int(user_id) if isinstance(user_id, int) or (isinstance(user_id, str) and user_id.isdigit()) else 1
            c.execute(
                "DELETE FROM watchlist WHERE userId = ? AND movieId = ?",
                (numeric_uid, movie_id)
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

        return True

    @staticmethod
    def is_in_watchlist(user_id: Any, movie_id: int, email: Optional[str] = None) -> bool:
        """Checks if a movie is in the user's Watchlist."""
        movie_id = int(movie_id)

        db = get_mongo_db()
        if db is not None:
            try:
                query: Dict[str, Any] = {"movieId": movie_id}
                if email:
                    query["$or"] = [{"userId": user_id}, {"email": email}]
                else:
                    query["userId"] = user_id
                if db.watchlist.find_one(query) is not None:
                    return True
            except Exception as e:
                print(f"[Mongo Watchlist Check Error] {e}")

        # SQLite check
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            numeric_uid = int(user_id) if isinstance(user_id, int) or (isinstance(user_id, str) and user_id.isdigit()) else 1
            c.execute(
                "SELECT 1 FROM watchlist WHERE userId = ? AND movieId = ?",
                (numeric_uid, movie_id)
            )
            row = c.fetchone()
            conn.close()
            return row is not None
        except Exception:
            return False

    @staticmethod
    def get_watchlist(user_id: Any, email: Optional[str] = None) -> List[int]:
        """Returns the list of movie IDs currently saved in the user's Watchlist."""
        db = get_mongo_db()
        if db is not None:
            try:
                query: Dict[str, Any] = {}
                if email:
                    query["$or"] = [{"userId": user_id}, {"email": email}]
                else:
                    query["userId"] = user_id
                cursor = db.watchlist.find(query).sort("added_at", -1)
                items = [int(doc["movieId"]) for doc in cursor if "movieId" in doc]
                if items:
                    return items
            except Exception as e:
                print(f"[Mongo Get Watchlist Error] {e}")

        # SQLite fallback
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            numeric_uid = int(user_id) if isinstance(user_id, int) or (isinstance(user_id, str) and user_id.isdigit()) else 1
            c.execute(
                "SELECT movieId FROM watchlist WHERE userId = ? ORDER BY added_at DESC",
                (numeric_uid,)
            )
            rows = c.fetchall()
            conn.close()
            return [int(r[0]) for r in rows]
        except Exception:
            return []

    @staticmethod
    def rate_movie(user_id: Any, movie_id: int, rating: float, email: Optional[str] = None) -> bool:
        """Stores or updates user rating for a movie (1.0 to 5.0) in MongoDB and SQLite."""
        movie_id = int(movie_id)
        rating = float(rating)
        ts = int(time.time())

        db = get_mongo_db()
        if db is not None:
            try:
                db.ratings.update_one(
                    {"userId": user_id, "movieId": movie_id},
                    {"$set": {
                        "userId": user_id,
                        "movieId": movie_id,
                        "rating": rating,
                        "email": email or "",
                        "timestamp": ts,
                        "updated_at": datetime.utcnow()
                    }},
                    upsert=True
                )
            except Exception as e:
                print(f"[Mongo Rate Error] {e}")

        # SQLite mirror
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            numeric_uid = int(user_id) if isinstance(user_id, int) or (isinstance(user_id, str) and user_id.isdigit()) else 1
            c.execute(
                """
                INSERT INTO ratings (userId, movieId, rating, timestamp)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(userId, movieId) DO UPDATE SET rating=excluded.rating, timestamp=excluded.timestamp
                """,
                (numeric_uid, movie_id, rating, ts)
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

        return True

    @staticmethod
    def get_user_rating(user_id: Any, movie_id: int, email: Optional[str] = None) -> Optional[float]:
        """Returns active user rating for a specific movie if present."""
        movie_id = int(movie_id)

        db = get_mongo_db()
        if db is not None:
            try:
                query: Dict[str, Any] = {"movieId": movie_id}
                if email:
                    query["$or"] = [{"userId": user_id}, {"email": email}]
                else:
                    query["userId"] = user_id
                doc = db.ratings.find_one(query)
                if doc and "rating" in doc:
                    return float(doc["rating"])
            except Exception as e:
                print(f"[Mongo Get Rating Error] {e}")

        # SQLite fallback
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            numeric_uid = int(user_id) if isinstance(user_id, int) or (isinstance(user_id, str) and user_id.isdigit()) else 1
            c.execute(
                "SELECT rating FROM ratings WHERE userId = ? AND movieId = ?",
                (numeric_uid, movie_id)
            )
            row = c.fetchone()
            conn.close()
            return float(row[0]) if row else None
        except Exception:
            return None

    @staticmethod
    def get_user_rated_movies(user_id: Any, email: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns all movies rated by this user."""
        db = get_mongo_db()
        if db is not None:
            try:
                query: Dict[str, Any] = {}
                if email:
                    query["$or"] = [{"userId": user_id}, {"email": email}]
                else:
                    query["userId"] = user_id
                cursor = db.ratings.find(query).sort("timestamp", -1)
                items = [
                    {"movieId": int(d["movieId"]), "rating": float(d["rating"]), "timestamp": int(d.get("timestamp", 0))}
                    for d in cursor if "movieId" in d and "rating" in d
                ]
                if items:
                    return items
            except Exception as e:
                print(f"[Mongo Get Rated Movies Error] {e}")

        # SQLite fallback
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            numeric_uid = int(user_id) if isinstance(user_id, int) or (isinstance(user_id, str) and user_id.isdigit()) else 1
            c.execute(
                "SELECT movieId, rating, timestamp FROM ratings WHERE userId = ? ORDER BY timestamp DESC",
                (numeric_uid,)
            )
            rows = c.fetchall()
            conn.close()
            return [{"movieId": int(r[0]), "rating": float(r[1]), "timestamp": int(r[2])} for r in rows]
        except Exception:
            return []

user_service = UserService()
