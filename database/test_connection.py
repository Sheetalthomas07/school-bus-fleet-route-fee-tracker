
from db_connection import get_connection

try:
    connection = get_connection()
    print("Database connected successfully!")
    print("Database location:", connection.execute("PRAGMA database_list").fetchone()[2])
    connection.close()

except Exception as e:
    print("Database connection failed:", e)

