"""
CreditLens - User Authentication & Profile Management Module
Stores and verifies user accounts in SQLite database with SHA-256 password hashing.
Supports multi-user sign-up, sign-in, and account switching.
"""

import os
import sqlite3
import hashlib
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "credit_lens.db")


def hash_password(password: str) -> str:
    """Returns SHA-256 hash of password string."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def init_user_db():
    """Initializes app_users table and seeds default accounts if not present."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS app_users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'Risk Analyst',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()

    # Seed default accounts if empty
    cursor.execute("SELECT COUNT(*) FROM app_users;")
    count = cursor.fetchone()[0]
    if count == 0:
        default_users = [
            ("admin", hash_password("password123"), "Chief Risk Administrator", "Chief Risk Officer"),
            ("analyst", hash_password("password123"), "Lead Credit Analyst", "Senior Risk Analyst"),
            ("guest", hash_password("guest123"), "Portfolio Reviewer", "Reviewer")
        ]
        cursor.executemany("""
        INSERT INTO app_users (username, password_hash, full_name, role)
        VALUES (?, ?, ?, ?);
        """, default_users)
        conn.commit()
    conn.close()


def register_user(username: str, password: str, full_name: str, role: str = "Risk Analyst"):
    """
    Registers a new user ID.
    Returns (success: bool, message: str)
    """
    init_user_db()
    username = username.strip().lower()
    if not username:
        return False, "Username cannot be empty."
    if len(password) < 4:
        return False, "Password must be at least 4 characters long."

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO app_users (username, password_hash, full_name, role)
        VALUES (?, ?, ?, ?);
        """, (username, hash_password(password), full_name.strip() or username.title(), role))
        conn.commit()
        return True, "Account created successfully!"
    except sqlite3.IntegrityError:
        return False, f"Username '@{username}' is already taken. Please choose another."
    except Exception as e:
        return False, f"Registration error: {e}"
    finally:
        conn.close()


def authenticate_user(username: str, password: str):
    """
    Authenticates username and password against SQLite.
    Returns user dict if valid, else None.
    """
    init_user_db()
    username = username.strip().lower()
    pw_hash = hash_password(password)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT user_id, username, full_name, role, created_at
    FROM app_users
    WHERE username = ? AND password_hash = ?;
    """, (username, pw_hash))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "user_id": row[0],
            "username": row[1],
            "full_name": row[2],
            "role": row[3],
            "created_at": row[4]
        }
    return None


def list_users():
    """Returns list of registered usernames and display names."""
    init_user_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username, full_name, role FROM app_users ORDER BY user_id ASC;")
    rows = cursor.fetchall()
    conn.close()
    return [{"username": r[0], "full_name": r[1], "role": r[2]} for r in rows]
