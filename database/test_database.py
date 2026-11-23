
from db_connection import get_connection

# Connect to database
connection = get_connection()
cursor = connection.cursor()

# Insert sample bus and route details
cursor.execute("""
    INSERT OR IGNORE INTO routes
    (route_name, bus_no, driver_name, driver_phone, max_capacity)
    VALUES (?, ?, ?, ?, ?)
""", ("Route 01", "KA01AB1234", "Sample Driver", "0000000000", 40))

# Get the route ID
cursor.execute("""
    SELECT route_id FROM routes
    WHERE route_name = ?
""", ("Route 01",))

route_id = cursor.fetchone()[0]

# Insert a bus stop
cursor.execute("""
    INSERT OR IGNORE INTO stops
    (route_id, stop_name, distance_km, term_fee)
    VALUES (?, ?, ?, ?)
""", (route_id, "Sample Stop", 5.0, 4000))


# Insert a student transport record
cursor.execute("""
    INSERT OR IGNORE INTO student_transport
    (reg_no, student_name, stop_id, fee_paid, dues, pass_valid_until)
    VALUES (?, ?, ?, ?, ?, ?)
""", ("DEMO001", "Sample Student", 1, 1000, 3000, "2027-03-31"))

connection.commit()

print("\nStudent Transport Details:")
cursor.execute("SELECT * FROM student_transport")
print(cursor.fetchall())


# Insert a fee payment record
cursor.execute("""
    INSERT INTO payments
    (alloc_id, amount, payment_date, payment_method)
    VALUES (?, ?, ?, ?)
""", (1, 1000, "2026-11-17", "UPI"))

connection.commit()

print("\nPayment Details:")
cursor.execute("SELECT * FROM payments")
print(cursor.fetchall())


connection.commit()

# Display inserted information
print("Bus and route details:")
cursor.execute("SELECT * FROM routes")
print(cursor.fetchall())

print("\nBus stop details:")
cursor.execute("SELECT * FROM stops")
print(cursor.fetchall())


# Display route and stop relationship
print("\nRoute and Stop Relationship:")

cursor.execute("""
    SELECT routes.route_name,
           routes.bus_no,
           stops.stop_name,
           stops.distance_km,
           stops.term_fee
    FROM routes
    INNER JOIN stops
    ON routes.route_id = stops.route_id
""")

for row in cursor.fetchall():
    print(row)


# Update student fee details
cursor.execute("""
    UPDATE student_transport
    SET fee_paid = (
        SELECT COALESCE(SUM(amount), 0)
        FROM payments
        WHERE payments.alloc_id = student_transport.alloc_id
    )
    WHERE alloc_id = 1
""")

cursor.execute("""
    UPDATE student_transport
    SET dues = (
        SELECT term_fee
        FROM stops
        WHERE stops.stop_id = student_transport.stop_id
    ) - fee_paid
    WHERE alloc_id = 1
""")

connection.commit()

print("\nUpdated Student Fee Details:")
cursor.execute("""
    SELECT student_name, fee_paid, dues
    FROM student_transport
    WHERE alloc_id = 1
""")
print(cursor.fetchall())


connection.close()
