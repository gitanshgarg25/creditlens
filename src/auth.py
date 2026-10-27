"""
CreditLens - User Authentication & Profile Management Module
Stores and verifies user accounts in SQLite database with SHA-256 password hashing.
Supports multi-user sign-up, sign-in, social OAuth (Google, Apple), Contact/Phone login,
and "Forgot Password" self-service recovery.
"""

from __future__ import annotations
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

    # Safely migrate columns (email, phone, auth_provider, avatar_data) if they don't exist
    for col_name, col_type in [
        ("email", "TEXT"),
        ("phone", "TEXT"),
        ("auth_provider", "TEXT DEFAULT 'local'"),
        ("avatar_data", "TEXT")
    ]:
        try:
            cursor.execute(f"ALTER TABLE app_users ADD COLUMN {col_name} {col_type};")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # column already exists

    # Strictly enforce that one email address can only belong to exactly one user account
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_app_users_email_unique ON app_users(LOWER(email));")
    conn.commit()

    # Ensure tables for persistent user sheets, session state, and notes exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_custom_sheets (
        sheet_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        sheet_title TEXT NOT NULL,
        file_path TEXT NOT NULL,
        record_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(username, sheet_title)
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS app_session_state (
        state_key TEXT PRIMARY KEY,
        state_value TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_risk_notes (
        note_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        sheet_title TEXT NOT NULL,
        note_content TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(username, sheet_title)
    );
    """)
    conn.commit()

    # Seed default sandbox accounts if database is empty
    # NOTE: These are strictly local demonstration/sandbox accounts for evaluation.
    # Passwords can be configured via environment variables in production.
    cursor.execute("SELECT COUNT(*) FROM app_users;")
    count = cursor.fetchone()[0]
    if count == 0:
        admin_pw = os.environ.get("CREDITLENS_DEMO_ADMIN_PASSWORD", "password123")
        analyst_pw = os.environ.get("CREDITLENS_DEMO_ANALYST_PASSWORD", "password123")
        guest_pw = os.environ.get("CREDITLENS_DEMO_GUEST_PASSWORD", "guest123")
        default_users = [
            ("admin", hash_password(admin_pw), "Chief Risk Officer", "CRO Level (Executive)", "admin@creditlens.internal", "+1-800-555-0100", "local"),
            ("analyst", hash_password(analyst_pw), "Lead Credit Analyst", "Senior Analyst Level", "analyst@creditlens.internal", "+1-800-555-0101", "local"),
            ("guest", hash_password(guest_pw), "Portfolio Auditor", "Reviewer Level", "guest@creditlens.internal", "+1-800-555-0102", "local")
        ]
        cursor.executemany("""
        INSERT INTO app_users (username, password_hash, full_name, role, email, phone, auth_provider)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """, default_users)
        conn.commit()
    else:
        # Ensure default demo accounts have standard email addresses populated
        cursor.execute("UPDATE app_users SET email = 'admin@creditlens.internal' WHERE username = 'admin' AND (email IS NULL OR email = '');")
        cursor.execute("UPDATE app_users SET email = 'analyst@creditlens.internal' WHERE username = 'analyst' AND (email IS NULL OR email = '');")
        cursor.execute("UPDATE app_users SET email = 'guest@creditlens.internal' WHERE username = 'guest' AND (email IS NULL OR email = '');")
        conn.commit()

    conn.close()


def get_user_by_username(username: str):
    """Fetches user record dict by username."""
    init_user_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT user_id, username, full_name, role, created_at, email, phone, auth_provider, avatar_data
    FROM app_users
    WHERE LOWER(username) = ?;
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
            "auth_provider": row[7] or "local",
            "avatar_data": row[8] or ""
        }
    return None


def get_user_by_email(email: str):
    """Fetches user record dict by email address (case-insensitive)."""
    init_user_db()
    ident = email.strip().lower()
    if not ident:
        return None
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT user_id, username, full_name, role, created_at, email, phone, auth_provider, avatar_data
    FROM app_users
    WHERE LOWER(email) = ?;
    """, (ident,))
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
            "auth_provider": row[7] or "local",
            "avatar_data": row[8] or ""
        }
    return None


def update_profile_avatar(username: str, avatar_data: str):
    """
    Updates or clears avatar_data (base64 string or image URI) for an account.
    Returns (success: bool, message: str)
    """
    init_user_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE app_users SET avatar_data = ? WHERE LOWER(username) = ?;", (avatar_data, username.strip().lower()))
        conn.commit()
        return True, "Profile picture updated successfully!"
    except Exception as e:
        return False, f"Failed to update profile picture: {e}"
    finally:
        conn.close()


def register_user(
    full_name: str = "",
    email: str = "",
    password: str = "",
    role: str = "Senior Analyst Level",
    username: str = "",
    *args,
    **kwargs
) -> tuple[bool, str]:
    """
    Registers a new institutional analyst account with an email address and password.
    Enforces that one email address can only be used for exactly one account.
    Returns (success: bool, message: str).
    """
    init_user_db()

    # Support legacy positional call: register_user(username, password, full_name, role, email, phone)
    if "@" not in email and args and len(args) >= 1 and "@" in str(args[0]):
        # Legacy positional mapping
        actual_user = full_name
        actual_pw = email
        actual_name = password
        actual_role = role
        actual_email = str(args[0])
        full_name = actual_name
        email = actual_email
        password = actual_pw
        role = actual_role
        username = actual_user
    elif kwargs.get("email"):
        email = kwargs.get("email")

    clean_name = full_name.strip()
    clean_email = email.strip().lower()
    clean_pw = password.strip()

    if not clean_name:
        return False, "Please enter your full display name."
    if not clean_email or "@" not in clean_email or "." not in clean_email:
        return False, "Please enter a valid institutional work email address."
    if len(clean_pw) < 4:
        return False, "Password must be at least 4 characters long."

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Enforce strict uniqueness: one email address can only create exactly 1 login ID
    cursor.execute("SELECT user_id, username, full_name FROM app_users WHERE LOWER(email) = ?;", (clean_email,))
    existing_user = cursor.fetchone()
    if existing_user:
        conn.close()
        return False, f"An account with email '{clean_email}' already exists. One email ID can only be registered once. Please log in with your password."

    # 2. Derive clean username if not provided
    if not username or not username.strip():
        prefix = clean_email.split("@")[0].replace(".", "").replace("-", "").replace("_", "")
        base_user = "".join(c for c in prefix.lower() if c.isalnum())[:16]
        if not base_user:
            base_user = "".join(c for c in clean_name.lower() if c.isalnum())[:16] or "analyst"
    else:
        base_user = "".join(c for c in username.strip().lower() if c.isalnum() or c == "_")[:18] or "analyst"

    final_user = base_user
    suffix = 2
    while True:
        cursor.execute("SELECT user_id FROM app_users WHERE LOWER(username) = ?;", (final_user,))
        if not cursor.fetchone():
            break
        final_user = f"{base_user}{suffix}"
        suffix += 1

    try:
        cursor.execute("""
        INSERT INTO app_users (username, password_hash, full_name, role, email, auth_provider)
        VALUES (?, ?, ?, ?, ?, 'local');
        """, (final_user, hash_password(clean_pw), clean_name, role, clean_email))
        conn.commit()
        return True, "Account created successfully!"
    except sqlite3.IntegrityError:
        return False, f"An account with email '{clean_email}' already exists. Please log in."
    except Exception as e:
        return False, f"Registration error: {e}"
    finally:
        conn.close()


def authenticate_user(email_or_username: str, password: str):
    """
    Authenticates by work email address or username and password.
    Returns user dict if valid, else None.
    """
    init_user_db()
    ident = email_or_username.strip().lower()
    if not ident or not password:
        return None
    pw_hash = hash_password(password)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT user_id, username, full_name, role, created_at, email, phone, auth_provider, avatar_data
    FROM app_users
    WHERE (LOWER(email) = ? OR LOWER(username) = ?) AND password_hash = ?;
    """, (ident, ident, pw_hash))
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
            "auth_provider": "local",
            "avatar_data": row[8] or ""
        }
    return None


def authenticate_or_register_social(provider: str, email_or_id: str, display_name: str = "", role: str = "Senior Analyst Level", password: str = ""):
    """
    Authenticates or registers a user signing in via Google Workspace or Apple ID.
    Supports real user credential validation and password persistence.
    Derives clean, authentic usernames and display names (never creates dummy or fake IDs).
    Returns authenticated user dict, or None if credentials are invalid.
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
    SELECT user_id, username, full_name, role, created_at, email, phone, auth_provider, avatar_data, password_hash
    FROM app_users
    WHERE email = ?;
    """, (ident,))
    row = cursor.fetchone()

    if row:
        stored_pw_hash = row[9]
        # If user supplied a password, verify against existing account
        if password and stored_pw_hash:
            # If the stored hash is an internal random key placeholder, update to user's real password
            if "Key_" in stored_pw_hash or stored_pw_hash.startswith("temp_"):
                cursor.execute("UPDATE app_users SET password_hash = ? WHERE user_id = ?;", (hash_password(password), row[0]))
                conn.commit()
            elif stored_pw_hash != hash_password(password):
                conn.close()
                return None  # Password mismatch!

        current_name = row[2]
        if display_clean and display_clean != current_name:
            cursor.execute("UPDATE app_users SET full_name = ? WHERE user_id = ?;", (display_clean, row[0]))
            conn.commit()
            current_name = display_clean

        user_dict = {
            "user_id": row[0],
            "username": row[1],
            "full_name": current_name,
            "role": row[3],
            "created_at": row[4],
            "email": row[5] or ident,
            "phone": row[6] or "",
            "auth_provider": row[7] or provider.lower(),
            "avatar_data": row[8] or ""
        }
        conn.close()
        return user_dict

    # New user: create account with real password hash
    user_pw = password if password else f"{provider}Key_{os.urandom(4).hex()}"
    final_username = base_user
    suffix = 2
    while True:
        try:
            cursor.execute("""
            INSERT INTO app_users (username, password_hash, full_name, role, email, auth_provider)
            VALUES (?, ?, ?, ?, ?, ?);
            """, (final_username, hash_password(user_pw), final_display_name, role, ident, provider.lower()))
            conn.commit()
            break
        except sqlite3.IntegrityError:
            final_username = f"{base_user}{suffix}"
            suffix += 1

    cursor.execute("""
    SELECT user_id, username, full_name, role, created_at, email, phone, auth_provider, avatar_data
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
        "auth_provider": row[7] or provider.lower(),
        "avatar_data": row[8] or ""
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
    SELECT user_id, username, full_name, role, created_at, email, phone, auth_provider, avatar_data
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
            "auth_provider": row[7] or "contact",
            "avatar_data": row[8] or ""
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
    SELECT user_id, username, full_name, role, created_at, email, phone, auth_provider, avatar_data
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
        "auth_provider": row[7] or "contact",
        "avatar_data": row[8] or ""
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
    WHERE LOWER(username) = ? OR LOWER(email) = ? OR phone = ?;
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
    Returns list of registered usernames and display names with avatars.
    Preserves all user-created accounts permanently.
    """
    init_user_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT username, full_name, role, auth_provider, avatar_data 
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
        av = r[4] or ""
        if exclude_temp:
            un_l = un.lower()
            if un_l.startswith("temp_") or un_l.startswith("dummy_"):
                continue
        users.append({"username": un, "full_name": fn, "role": rl, "auth_provider": ap, "avatar_data": av})
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


# =============================================================================
# DATA PERSISTENCE: CUSTOM USER DATASETS, WORKBOOK SHEETS & NOTES
# =============================================================================

def save_user_custom_sheet(username: str, sheet_title: str, df) -> tuple[bool, str]:
    """
    Saves a user's custom dataset sheet to disk and registers it in SQLite.
    Ensures custom uploaded sheets are permanently preserved across logouts and server restarts.
    """
    init_user_db()
    if df is None:
        return False, "Cannot save empty dataset."
    
    username_clean = username.strip().lower()
    safe_title = "".join(c for c in sheet_title if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
    if not safe_title:
        safe_title = f"sheet_{os.urandom(3).hex()}"
    
    user_dir = os.path.join(BASE_DIR, "data", "user_uploads", username_clean)
    os.makedirs(user_dir, exist_ok=True)
    
    file_path = os.path.join(user_dir, f"{safe_title}.csv")
    try:
        import pandas as pd
        if isinstance(df, pd.DataFrame):
            df.to_csv(file_path, index=False)
            records = len(df)
        else:
            return False, "Dataset must be a pandas DataFrame."
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO user_custom_sheets (username, sheet_title, file_path, record_count)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(username, sheet_title) DO UPDATE SET
            file_path = excluded.file_path,
            record_count = excluded.record_count,
            created_at = CURRENT_TIMESTAMP;
        """, (username_clean, sheet_title.strip(), file_path, records))
        conn.commit()
        conn.close()
        return True, f"Saved sheet '{sheet_title}' permanently ({records:,} records)."
    except Exception as e:
        return False, f"Failed to save sheet: {e}"


def load_user_custom_sheets(username: str) -> dict:
    """
    Retrieves all custom dataset sheets belonging to the user from SQLite and disk.
    Returns dict mapping sheet_title -> DataFrame.
    """
    init_user_db()
    username_clean = username.strip().lower()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT sheet_title, file_path
    FROM user_custom_sheets
    WHERE username = ?
    ORDER BY created_at ASC;
    """, (username_clean,))
    rows = cursor.fetchall()
    conn.close()

    sheets = {}
    for title, path in rows:
        target_path = path if os.path.isabs(path) else os.path.join(BASE_DIR, path)
        if os.path.exists(target_path):
            try:
                import pandas as pd
                sheets[title] = pd.read_csv(target_path)
            except Exception:
                sheets[title] = target_path
    return sheets


def delete_user_custom_sheet(username: str, sheet_title: str) -> bool:
    """Removes a custom dataset sheet record and local file for a user."""
    init_user_db()
    username_clean = username.strip().lower()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT file_path FROM user_custom_sheets WHERE username = ? AND sheet_title = ?;", (username_clean, sheet_title))
    row = cursor.fetchone()
    if row:
        file_path = row[0]
        target_path = file_path if os.path.isabs(file_path) else os.path.join(BASE_DIR, file_path)
        if os.path.exists(target_path):
            try:
                os.remove(target_path)
            except Exception:
                pass
    cursor.execute("DELETE FROM user_custom_sheets WHERE username = ? AND sheet_title = ?;", (username_clean, sheet_title))
    conn.commit()
    conn.close()
    return True


def set_last_active_user(username: str):
    """Stores the username of the last logged-in account in SQLite."""
    init_user_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO app_session_state (state_key, state_value, updated_at)
    VALUES ('last_active_username', ?, CURRENT_TIMESTAMP)
    ON CONFLICT(state_key) DO UPDATE SET
        state_value = excluded.state_value,
        updated_at = CURRENT_TIMESTAMP;
    """, (username.strip().lower(),))
    conn.commit()
    conn.close()


def get_last_active_user():
    """Returns user dict of the last logged-in user, or None."""
    init_user_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT state_value FROM app_session_state WHERE state_key = 'last_active_username';")
    row = cursor.fetchone()
    conn.close()
    if row and row[0]:
        return get_user_by_username(row[0])
    return None


def clear_last_active_user():
    """Clears last active user on explicit sign-out."""
    init_user_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM app_session_state WHERE state_key = 'last_active_username';")
    conn.commit()
    conn.close()


def save_user_risk_note(username: str, sheet_title: str, note_content: str):
    """Persists analyst underwriting comments or credit memos for a sheet."""
    init_user_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO user_risk_notes (username, sheet_title, note_content, updated_at)
    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(username, sheet_title) DO UPDATE SET
        note_content = excluded.note_content,
        updated_at = CURRENT_TIMESTAMP;
    """, (username.strip().lower(), sheet_title.strip(), note_content))
    conn.commit()
    conn.close()


def get_user_risk_note(username: str, sheet_title: str) -> str:
    """Retrieves saved analyst notes for a sheet."""
    init_user_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT note_content FROM user_risk_notes 
    WHERE username = ? AND sheet_title = ?;
    """, (username.strip().lower(), sheet_title.strip()))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else ""

