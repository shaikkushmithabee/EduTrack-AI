import hashlib
import os
import sqlite3
from database import get_connection, get_student_by_reg_no, get_student_by_email


def hash_password(password: str, salt: str = None) -> str:
    """Generate salted SHA-256 password hash."""
    if not salt:
        salt = os.urandom(16).hex()
    hash_obj = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return f"{salt}${hash_obj.hex()}"


def verify_password(stored_password_hash: str, provided_password: str) -> bool:
    """Verify password against stored salt and hash."""
    try:
        salt, expected_hash = stored_password_hash.split('$')
        new_hash = hashlib.pbkdf2_hmac(
            'sha256',
            provided_password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
        return new_hash == expected_hash
    except Exception:
        return False


def create_user(username, email, password, role, full_name, student_reg_no=None):
    """Create a new user account with hashed password."""
    username = username.strip().lower()
    email = email.strip().lower()
    if role not in ('Admin', 'Faculty', 'Student'):
        return False, "Invalid role. Must be Admin, Faculty, or Student."

    if role == 'Student' and not student_reg_no:
        return False, "Student account must be linked to a Registration Number."

    conn = get_connection()
    try:
        pwd_hash = hash_password(password)
        conn.execute("""
            INSERT INTO users (username, email, password_hash, role, student_reg_no, full_name)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (username, email, pwd_hash, role, student_reg_no.strip().upper() if student_reg_no else None, full_name.strip()))
        conn.commit()
        return True, f"User {username} created successfully as {role}."
    except sqlite3.IntegrityError as e:
        if "username" in str(e).lower():
            return False, f"Username '{username}' already exists."
        elif "email" in str(e).lower():
            return False, f"Email '{email}' already registered."
        return False, f"Integrity error: {e}"
    except Exception as e:
        return False, f"Error creating user: {e}"
    finally:
        conn.close()


def authenticate_user(identifier, password):
    """
    Authenticate by username, email, or student registration number.
    Returns (user_dict or None, message: str)
    """
    if not identifier or not password:
        return None, "Please provide both identifier and password."

    ident = identifier.strip().lower()
    conn = get_connection()
    try:
        # Check by username, email, or student_reg_no
        user = conn.execute("""
            SELECT * FROM users
            WHERE LOWER(username) = ? OR LOWER(email) = ? OR UPPER(student_reg_no) = UPPER(?)
        """, (ident, ident, ident.upper())).fetchone()

        if not user:
            return None, "Account not found."

        user_dict = dict(user)
        if verify_password(user_dict["password_hash"], password):
            # Do not leak hash in session
            del user_dict["password_hash"]
            return user_dict, "Login successful."
        else:
            return None, "Invalid password."
    finally:
        conn.close()


def ensure_bootstrap_admin():
    """Ensure at least one admin account exists so the system can be configured."""
    conn = get_connection()
    admin_count = conn.execute("SELECT COUNT(*) as cnt FROM users WHERE role = 'Admin'").fetchone()["cnt"]
    if admin_count == 0:
        pwd_hash = hash_password("Admin@123")
        conn.execute("""
            INSERT INTO users (username, email, password_hash, role, full_name)
            VALUES ('admin', 'admin@edutrack.ac.in', ?, 'Admin', 'Institutional Administrator')
        """, (pwd_hash,))
        conn.commit()
    conn.close()


def get_all_users(role=None):
    conn = get_connection()
    query = "SELECT id, username, email, role, student_reg_no, full_name, created_at FROM users"
    params = []
    if role:
        query += " WHERE role = ?"
        params.append(role)
    query += " ORDER BY role, username ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_user(user_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return True, "User deleted."
    except Exception as e:
        return False, f"Error: {e}"
    finally:
        conn.close()
