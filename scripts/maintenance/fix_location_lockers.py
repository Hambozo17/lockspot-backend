import mysql.connector
import sys

# Database connection
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Hambz',
    database='lockspot'
)
cursor = conn.cursor()

# Check location 1
cursor.execute("SELECT id, name FROM lockers_lockerlocation WHERE id = 1")
location = cursor.fetchone()
if not location:
    print("Location 1 doesn't exist!")
    sys.exit(1)

print(f"Location 1: {location[1]}")

# Check current lockers
cursor.execute("SELECT COUNT(*) FROM lockers_lockerunit WHERE location_id = 1")
current_count = cursor.fetchone()[0]
print(f"Current locker count: {current_count}")

if current_count == 0:
    print("\nAdding 15 lockers to location 1...")
    
    # Add lockers
    lockers = []
    for i in range(1, 16):
        if i <= 5:
            size = 'Small'
            unit = f'SZ-S{i:02d}'
        elif i <= 10:
            size = 'Medium'
            unit = f'SZ-M{i-5:02d}'
        else:
            size = 'Large'
            unit = f'SZ-L{i-10:02d}'
        
        lockers.append((1, unit, size, 'Available'))
    
    cursor.executemany(
        "INSERT INTO lockers_lockerunit (location_id, unit_number, size, status) VALUES (%s, %s, %s, %s)",
        lockers
    )
    conn.commit()
    print(f"✅ Added {len(lockers)} lockers")
else:
    print("✅ Location 1 already has lockers")

# Verify
cursor.execute("SELECT COUNT(*), size FROM lockers_lockerunit WHERE location_id = 1 AND status = 'Available' GROUP BY size")
print("\nAvailable lockers by size:")
for count, size in cursor.fetchall():
    print(f"  {size}: {count}")

cursor.close()
conn.close()
