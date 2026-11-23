import hashlib
import hmac
import secrets
import sqlite3

from database.db_connection import get_connection


PASSWORD_ITERATIONS = 310_000
PASSWORD_SALT_BYTES = 16
MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 64
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 1024
_DUMMY_SALT = b"school-transport-login-check"


def has_admin_account():

    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM admin_accounts LIMIT 1")
        return cursor.fetchone() is not None
    finally:
        connection.close()


def _password_digest(password, salt, iterations):

    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations
    )


def create_admin_account(username, password):

    username = username.strip()
    if not MIN_USERNAME_LENGTH <= len(username) <= MAX_USERNAME_LENGTH:
        raise ValueError(
            f"Username must be {MIN_USERNAME_LENGTH} to "
            f"{MAX_USERNAME_LENGTH} characters."
        )
    if not MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH:
        raise ValueError(
            f"Password must be {MIN_PASSWORD_LENGTH} to "
            f"{MAX_PASSWORD_LENGTH} characters."
        )

    salt = secrets.token_bytes(PASSWORD_SALT_BYTES)
    password_hash = _password_digest(
        password,
        salt,
        PASSWORD_ITERATIONS
    )

    connection = get_connection()
    try:
        connection.execute("BEGIN IMMEDIATE")
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM admin_accounts LIMIT 1")
        if cursor.fetchone() is not None:
            connection.rollback()
            raise ValueError(
                "An administrator account already exists."
            )
        cursor.execute("""
            INSERT INTO admin_accounts (
                username,
                password_salt,
                password_hash,
                password_iterations
            )
            VALUES (?, ?, ?, ?)
        """, (
            username,
            salt,
            password_hash,
            PASSWORD_ITERATIONS
        ))
        connection.commit()
    except sqlite3.Error:
        connection.rollback()
        raise
    finally:
        connection.close()


def verify_admin_credentials(username, password):

    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT password_salt, password_hash, password_iterations
            FROM admin_accounts
            WHERE username = ?
        """, (username.strip(),))
        account = cursor.fetchone()
    finally:
        connection.close()

    if account is None:
        candidate = _password_digest(
            password,
            _DUMMY_SALT,
            PASSWORD_ITERATIONS
        )
        hmac.compare_digest(candidate, bytes(PASSWORD_SALT_BYTES * 2))
        return False

    salt, expected_hash, iterations = account
    candidate = _password_digest(password, salt, iterations)
    return hmac.compare_digest(candidate, expected_hash)
