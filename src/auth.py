"""
CreditLens - User Authentication & Profile Management Module
Stores and verifies user accounts in SQLite database with SHA-256 password hashing.
Supports multi-user sign-up, sign-in, social OAuth (Google, Apple), Contact/Phone login,
and "Forgot Password" self-service recovery.
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
    """Initializes app_users table, adds columns if missing, and seeds default accounts."""
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

    # Safely migrate new columns (email, phone, auth_provider) if they don't exist
    for col_name, col_type in [
        ("email", "TEXT"),
        ("phone", "TEXT"),
        ("auth_provider", "TEXT DEFAULT 'local'")
    ]:
        try:
            cursor.execute(f"ALTER TABLE app_users ADD COLUMN {col_name} {col_type};")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # column already exists

    # Purge any legacy temporary or test accounts
    cursor.execute("""
    DELETE FROM app_users 
    WHERE username LIKE 'mobile_%' 
       OR username LIKE 'user_%' 
       OR username LIKE 'temp_%' 
       OR username LIKE 'test_%'
       OR username LIKE '%_demo'
       OR username LIKE '%_user'
       OR username = 'officer_apple'
       OR username = 'analyst_google';
    """)
    conn.commit()

    # Seed default accounts if empty
    cursor.execute("SELECT COUNT(*) FROM app_users;")
    count = cursor.fetchone()[0]
    if count == 0:
        default_users = [
            ("admin", hash_password("password123"), "Chief Risk Officer", "CRO Level (Executive)", "admin@creditlens.internal", "+1-800-555-0100", "local"),
            ("analyst", hash_password("password123"), "Lead Credit Analyst", "Senior Analyst Level", "analyst@creditlens.internal", "+1-800-555-0101", "local"),
            ("guest", hash_password("guest123"), "Portfolio Auditor", "Reviewer Level", "guest@creditlens.internal", "+1-800-555-0102", "local")
        ]
        cursor.executemany("""
        INSERT INTO app_users (username, password_hash, full_name, role, email, phone, auth_provider)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """, default_users)
        conn.commit()
    conn.close()


def get_user_by_username(username: str):
    """Fetches user record dict by username."""
    init_user_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT user_id, username, full_name, role, created_at, email, phone, auth_provider
    FROM app_users
    WHERE username = ?;
    """, (username.strip().lower(),))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "user_id": row[0],
            "username": row[1],
            "full_name": row[2],
            "role": row[3],
            "created_at": row[4],
            "email": row[5] or "",
            "phone": row[6] or "",
            "auth_provider": row[7] or "local"
        }
    return None


def register_user(username: str, password: str, full_name: str, role: str = "Risk Analyst", email: str = "", phone: str = "", auth_provider: str = "local"):
    """
    Registers a new user ID with optional email and phone.
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
        INSERT INTO app_users (username, password_hash, full_name, role, email, phone, auth_provider)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (username, hash_password(password), full_name.strip() or username.title(), role, email.strip().lower(), phone.strip(), auth_provider))
        conn.commit()
        return True, "Account created successfully!"
    except sqlite3.IntegrityError:
        return False, f"Username '@{username}' is already taken. Please choose another."
    except Exception as e:
        return False, f"Registration error: {e}"
    finally:
        conn.close()


def authenticate_user(username_or_email: str, password: str):
    """
    Authenticates username, email, or contact phone against SQLite.
    Returns user dict if valid, else None.
    """
    init_user_db()
    ident = username_or_email.strip().lower()
    pw_hash = hash_password(password)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT user_id, username, full_name, role, created_at, email, phone, auth_provider
    FROM app_users
    WHERE (username = ? OR email = ? OR phone = ?) AND password_hash = ?;
    """, (ident, ident, ident, pw_hash))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "user_id": row[0],
            "username": row[1],
            "full_name": row[2],
            "role": row[3],
            "created_at": row[4],
            "email": row[5] or "",
            "phone": row[6] or "",
            "auth_provider": row[7] or "local"
        }
    return None


def authenticate_or_register_social(provider: str, email_or_id: str, display_name: str = "", role: str = "Senior Analyst Level"):
    """
    Authenticates or instantly registers a user signing in via Google Workspace or Apple ID.
    Derives clean, authentic usernames and display names (never creates dummy or fake IDs).
    Returns authenticated user dict.
    """
    init_user_db()
    ident = email_or_id.strip().lower()
    if not ident:
        return None

    # Derive clean institutional username
    display_clean = display_name.strip()
    if display_clean:
        base_user = "".join(c for c in display_clean.lower() if c.isalnum())[:18]
    else:
        email_prefix = ident.split("@")[0].replace(".", "").replace("-", "").replace("_", "")
        base_user = "".join(c for c in email_prefix.lower() if c.isalnum())[:18]

    if not base_user:
        base_user = "officer"

    final_display_name = display_clean or (ident.split("@")[0].replace(".", " ").replace("_", " ").title())

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT user_id, username, full_name, role, created_at, email, phone, auth_provider
    FROM app_users
    WHERE email = ? OR username = ?;
    """, (ident, base_user))
    row = cursor.fetchone()

    if row:
        user_dict = {
            "user_id": row[0],
            "username": row[1],
            "full_name": row[2],
            "role": row[3],
            "created_at": row[4],
            "email": row[5] or ident,
            "phone": row[6] or "",
            "auth_provider": row[7] or provider.lower()
        }
        conn.close()
        return user_dict

    # New user: auto-create account with clean username
    random_pw = f"{provider}Key_{os.urandom(4).hex()}"
    final_username = base_user
    suffix = 2
    while True:
        try:
            cursor.execute("""
            INSERT INTO app_users (username, password_hash, full_name, role, email, auth_provider)
            VALUES (?, ?, ?, ?, ?, ?);
            """, (final_username, hash_password(random_pw), final_display_name, role, ident, provider.lower()))
            conn.commit()
            break
        except sqlite3.IntegrityError:
            final_username = f"{base_user}{suffix}"
            suffix += 1

    cursor.execute("""
    SELECT user_id, username, full_name, role, created_at, email, phone, auth_provider
    FROM app_users
    WHERE username = ?;
    """, (final_username,))
    row = cursor.fetchone()
    conn.close()

    return {
        "user_id": row[0],
        "username": row[1],
        "full_name": row[2],
        "role": row[3],
        "created_at": row[4],
        "email": row[5] or ident,
        "phone": row[6] or "",
        "auth_provider": row[7] or provider.lower()
    }


def authenticate_or_register_contact(phone: str, full_name: str = "", role: str = "Senior Analyst Level", preferred_id: str = ""):
    """
    Authenticates or registers a user signing in via Mobile / Contact number.
    Derives clean professional username (from preferred_id, full_name, or sanitized name).
    Never produces temporary, fake, or dummy IDs (no mobile_XXXXXX).
    """
    init_user_db()
    phone_clean = phone.strip()
    if not phone_clean:
        return None

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT user_id, username, full_name, role, created_at, email, phone, auth_provider
    FROM app_users
    WHERE phone = ?;
    """, (phone_clean,))
    row = cursor.fetchone()

    if row:
        user_dict = {
            "user_id": row[0],
            "username": row[1],
            "full_name": row[2],
            "role": row[3],
            "created_at": row[4],
            "email": row[5] or "",
            "phone": row[6] or phone_clean,
            "auth_provider": row[7] or "contact"
        }
        conn.close()
        return user_dict

    clean_name = full_name.strip()
    clean_pref = preferred_id.strip().lower()

    if clean_pref:
        base_user = "".join(c for c in clean_pref if c.isalnum() or c == "_")[:18]
    elif clean_name:
        base_user = "".join(c for c in clean_name.lower() if c.isalnum())[:18]
    else:
        digits_only = "".join(c for c in phone_clean if c.isdigit())[-4:] or "01"
        base_user = f"officer{digits_only}"

    if not base_user:
        base_user = "officer"

    final_display_name = clean_name or f"Credit Officer ({phone_clean[-4:]})"
    random_pw = f"Pass_{os.urandom(4).hex()}"
    final_username = base_user
    suffix = 2
    while True:
        try:
            cursor.execute("""
            INSERT INTO app_users (username, password_hash, full_name, role, phone, auth_provider)
            VALUES (?, ?, ?, ?, ?, ?);
            """, (final_username, hash_password(random_pw), final_display_name, role, phone_clean, "contact"))
            conn.commit()
            break
        except sqlite3.IntegrityError:
            final_username = f"{base_user}{suffix}"
            suffix += 1

    cursor.execute("""
    SELECT user_id, username, full_name, role, created_at, email, phone, auth_provider
    FROM app_users
    WHERE username = ?;
    """, (final_username,))
    row = cursor.fetchone()
    conn.close()

    return {
        "user_id": row[0],
        "username": row[1],
        "full_name": row[2],
        "role": row[3],
        "created_at": row[4],
        "email": row[5] or "",
        "phone": row[6] or phone_clean,
        "auth_provider": row[7] or "contact"
    }


def reset_password_forgot(identifier: str, new_password: str):
    """
    Self-service Forgot Password reset:
    Finds account by username, email, or contact number, and updates to new password.
    Returns (success: bool, message: str)
    """
    init_user_db()
    ident = identifier.strip().lower()
    if not ident:
        return False, "Please enter your username, email, or contact number."
    if len(new_password) < 4:
        return False, "New password must be at least 4 characters long."

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT user_id, username, full_name
    FROM app_users
    WHERE username = ? OR email = ? OR phone = ?;
    """, (ident, ident, ident))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return False, f"No existing account found with identifier '{identifier}'."

    u_id, username, full_name = row
    try:
        pw_hash = hash_password(new_password)
        cursor.execute("UPDATE app_users SET password_hash = ? WHERE user_id = ?;", (pw_hash, u_id))
        conn.commit()
        return True, f"Password successfully reset for @{username} ({full_name})! You can now log in."
    except Exception as e:
        return False, f"Failed to reset password: {e}"
    finally:
        conn.close()


def list_users(exclude_temp: bool = True):
    """
    Returns list of registered usernames and display names.
    By default excludes temporary test IDs (e.g. mobile_*, user_*, *_demo).
    """
    init_user_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT username, full_name, role, auth_provider 
    FROM app_users 
    ORDER BY CASE 
        WHEN username = 'admin' THEN 1
        WHEN username = 'analyst' THEN 2
        WHEN username = 'guest' THEN 3
        ELSE 4 
    END, user_id ASC;
    """)
    rows = cursor.fetchall()
    conn.close()
    
    users = []
    for r in rows:
        un, fn, rl, ap = r[0], r[1], r[2], r[3] or "local"
        if exclude_temp:
            un_l = un.lower()
            if (un_l.startswith("mobile_") or un_l.startswith("user_") or 
                un_l.startswith("temp_") or un_l.startswith("test_") or 
                un_l.endswith("_demo") or un_l.endswith("_user") or
                "demo" in un_l or "dummy" in un_l or "fake" in un_l or
                un_l in ("officer_apple", "analyst_google")):
                continue
        users.append({"username": un, "full_name": fn, "role": rl, "auth_provider": ap})
    return users


def update_password(username: str, new_password: str):
    """
    Updates the password for an existing user account.
    Returns (success: bool, message: str)
    """
    init_user_db()
    username = username.strip().lower()
    if len(new_password) < 4:
        return False, "New password must be at least 4 characters long."

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        pw_hash = hash_password(new_password)
        cursor.execute("UPDATE app_users SET password_hash = ? WHERE username = ?;", (pw_hash, username))
        conn.commit()
        if cursor.rowcount > 0:
            return True, f"Password for @{username} updated successfully!"
        return False, f"User @{username} not found."
    except Exception as e:
        return False, f"Failed to update password: {e}"
    finally:
        conn.close()
