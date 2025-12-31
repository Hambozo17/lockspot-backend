"""Check who has signed in to LockSpot"""
import mysql.connector
from datetime import datetime

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Hambz',
    database='lockspot'
)

cursor = conn.cursor(dictionary=True)

print("\n" + "="*70)
print("USERS IN LOCKSPOT DATABASE")
print("="*70)

cursor.execute("""
    SELECT id, email, first_name, last_name, phone, 
           last_login, created_at, is_active
    FROM auth_user 
    ORDER BY created_at DESC
""")

users = cursor.fetchall()

for i, user in enumerate(users, 1):
    print(f"\n{i}. USER DETAILS:")
    print(f"   ID: {user['id']}")
    print(f"   Email: {user['email']}")
    print(f"   Name: {user['first_name']} {user['last_name']}")
    print(f"   Phone: {user['phone']}")
    print(f"   Last Login: {user['last_login'] or 'Never'}")
    print(f"   Account Created: {user['created_at']}")
    print(f"   Status: {'Active' if user['is_active'] else 'Inactive'}")
    print("-"*70)

# Check recent bookings
print("\n" + "="*70)
print("RECENT ACTIVITY (Bookings)")
print("="*70)

cursor.execute("""
    SELECT b.id, u.email, b.status, b.total_amount, b.created_at
    FROM lockers_booking b
    JOIN auth_user u ON b.user_id = u.id
    ORDER BY b.created_at DESC
    LIMIT 5
""")

bookings = cursor.fetchall()

if bookings:
    for booking in bookings:
        print(f"\nBooking ID: {booking['id']}")
        print(f"User: {booking['email']}")
        print(f"Status: {booking['status']}")
        print(f"Amount: SAR {booking['total_amount']}")
        print(f"Created: {booking['created_at']}")
else:
    print("\nNo bookings yet")

cursor.close()
conn.close()

print("\n" + "="*70)
