import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Hambz',
    database='lockspot'
)
cursor = conn.cursor()

# Get all locations
cursor.execute("SELECT id, name FROM lockers_lockerlocation")
locations = cursor.fetchall()

print(f"Found {len(locations)} locations:")
for loc_id, name in locations:
    cursor.execute("SELECT COUNT(*) FROM lockers_lockerunit WHERE location_id = %s AND status = 'Available'", (loc_id,))
    count = cursor.fetchone()[0]
    print(f"  ID {loc_id}: {name} - {count} available lockers")

print("\n" + "="*60)
print("Adding 15 lockers to each location with 0 lockers...")
print("="*60 + "\n")

for loc_id, name in locations:
    cursor.execute("SELECT COUNT(*) FROM lockers_lockerunit WHERE location_id = %s", (loc_id,))
    current_count = cursor.fetchone()[0]
    
    if current_count == 0:
        print(f"Adding lockers to '{name}' (ID {loc_id})...")
        lockers = []
        for i in range(1, 16):
            if i <= 5:
                size = 'Small'
                unit = f'LOC{loc_id}-S{i:02d}'
            elif i <= 10:
                size = 'Medium'
                unit = f'LOC{loc_id}-M{i-5:02d}'
            else:
                size = 'Large'
                unit = f'LOC{loc_id}-L{i-10:02d}'
            
            lockers.append((loc_id, unit, size, 'Available'))
        
        cursor.executemany(
            "INSERT INTO lockers_lockerunit (location_id, unit_number, size, status) VALUES (%s, %s, %s, %s)",
            lockers
        )
        print(f"  ✅ Added {len(lockers)} lockers")

conn.commit()

# Final count
cursor.execute("""
    SELECT l.id, l.name, COUNT(u.id) as locker_count
    FROM lockers_lockerlocation l
    LEFT JOIN lockers_lockerunit u ON l.id = u.location_id AND u.status = 'Available'
    GROUP BY l.id, l.name
    ORDER BY l.id
""")

print("\n" + "="*60)
print("FINAL STATUS:")
print("="*60)
for loc_id, name, count in cursor.fetchall():
    print(f"  ID {loc_id}: {name} - {count} available lockers")

cursor.close()
conn.close()
