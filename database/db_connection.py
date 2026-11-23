
import sqlite3
import os

# Get the main project folder path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Define the database file location
DB_PATH = os.path.join(BASE_DIR, "school_transport.db")


def get_connection():
    """Create and return a database connection."""
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection
