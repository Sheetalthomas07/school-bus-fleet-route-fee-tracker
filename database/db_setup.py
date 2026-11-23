
if __package__:
    from .db_connection import get_connection
else:
    from db_connection import get_connection


def create_tables():
    connection = get_connection()
    cursor = connection.cursor()

    # Create routes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS routes (
            route_id INTEGER PRIMARY KEY AUTOINCREMENT,
            route_name TEXT NOT NULL UNIQUE,
            start_point TEXT,
            end_point TEXT,
            bus_no TEXT NOT NULL UNIQUE,
            driver_name TEXT NOT NULL,
            driver_phone TEXT NOT NULL,
            max_capacity INTEGER NOT NULL CHECK(max_capacity > 0)
        )
    """)

    cursor.execute("PRAGMA table_info(routes)")
    route_columns = {column[1] for column in cursor.fetchall()}
    if "start_point" not in route_columns:
        cursor.execute("ALTER TABLE routes ADD COLUMN start_point TEXT")
    if "end_point" not in route_columns:
        cursor.execute("ALTER TABLE routes ADD COLUMN end_point TEXT")

    # Create stops table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stops (
            stop_id INTEGER PRIMARY KEY AUTOINCREMENT,
            route_id INTEGER NOT NULL,
            stop_name TEXT NOT NULL,
            distance_km REAL NOT NULL CHECK(distance_km >= 0),
            term_fee REAL NOT NULL CHECK(term_fee >= 0),

            FOREIGN KEY (route_id)
            REFERENCES routes(route_id)
            ON DELETE RESTRICT,

            UNIQUE(route_id, stop_name)
        )
    """)


    # Create student_transport table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_transport (
            alloc_id INTEGER PRIMARY KEY AUTOINCREMENT,
            reg_no TEXT NOT NULL UNIQUE,
            student_name TEXT NOT NULL,
            stop_id INTEGER NOT NULL,
            fee_paid REAL NOT NULL DEFAULT 0 CHECK(fee_paid >= 0),
            dues REAL NOT NULL DEFAULT 0 CHECK(dues >= 0),
            credit_balance REAL NOT NULL DEFAULT 0 CHECK(credit_balance >= 0),
            pass_valid_until TEXT,
            transport_status TEXT NOT NULL DEFAULT 'Active'
                CHECK(transport_status IN ('Active', 'Discontinued')),

            FOREIGN KEY (stop_id)
            REFERENCES stops(stop_id)
            ON DELETE RESTRICT
        )
    """)

    cursor.execute("PRAGMA table_info(student_transport)")
    student_transport_columns = {
        column[1] for column in cursor.fetchall()
    }
    if "credit_balance" not in student_transport_columns:
        cursor.execute("""
            ALTER TABLE student_transport
            ADD COLUMN credit_balance REAL NOT NULL DEFAULT 0
                CHECK(credit_balance >= 0)
        """)
        cursor.execute("""
            UPDATE student_transport
            SET dues = MAX(
                    COALESCE((
                        SELECT term_fee
                        FROM stops
                        WHERE stops.stop_id = student_transport.stop_id
                    ), 0) - fee_paid,
                    0
                ),
                credit_balance = MAX(
                    fee_paid - COALESCE((
                        SELECT term_fee
                        FROM stops
                        WHERE stops.stop_id = student_transport.stop_id
                    ), 0),
                    0
                )
        """)

    if "transport_status" not in student_transport_columns:
        cursor.execute("""
            ALTER TABLE student_transport
            ADD COLUMN transport_status TEXT NOT NULL DEFAULT 'Active'
                CHECK(transport_status IN ('Active', 'Discontinued'))
        """)

    # Create payments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            alloc_id INTEGER NOT NULL,
            amount REAL NOT NULL CHECK(amount > 0),
            payment_date TEXT NOT NULL,
            payment_method TEXT NOT NULL,

            FOREIGN KEY (alloc_id)
            REFERENCES student_transport(alloc_id)
            ON DELETE RESTRICT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_accounts (
            admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL COLLATE NOCASE UNIQUE,
            password_salt BLOB NOT NULL,
            password_hash BLOB NOT NULL,
            password_iterations INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)



    connection.commit()
    connection.close()

    print("Routes table created successfully!")


if __name__ == "__main__":
    create_tables()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
    """)

    print("Database tables:")
    for table in cursor.fetchall():
        print("-", table[0])

    connection.close()