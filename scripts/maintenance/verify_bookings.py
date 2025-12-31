import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Hambz',
    database='lockspot'
)

cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM lockers_booking WHERE status="Active"')
print(f'Active bookings: {cursor.fetchone()[0]}')

cursor.execute('SELECT id, user_id, locker_id, total_amount, status FROM lockers_booking ORDER BY id DESC LIMIT 3')
print('\nLatest bookings:')
for r in cursor.fetchall():
    print(f'  ID: {r[0]}, User: {r[1]}, Locker: {r[2]}, Amount: ${r[3]}, Status: {r[4]}')

cursor.execute('SELECT COUNT(*) FROM lockers_lockerunit WHERE status="Booked"')
print(f'\nBooked lockers: {cursor.fetchone()[0]}')

cursor.execute('SELECT COUNT(*) FROM lockers_lockerunit WHERE status="Available"')
print(f'Available lockers: {cursor.fetchone()[0]}')

conn.close()
