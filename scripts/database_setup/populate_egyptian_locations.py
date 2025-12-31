import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Hambz',
    database='lockspot'
)

cursor = conn.cursor()

# Add more Egyptian locations
print("Adding Egyptian locations...")

# Get or create pricing tiers first
cursor.execute("SELECT id FROM lockers_pricingtier WHERE size='Small' LIMIT 1")
small_tier = cursor.fetchone()
cursor.execute("SELECT id FROM lockers_pricingtier WHERE size='Medium' LIMIT 1")
medium_tier = cursor.fetchone()
cursor.execute("SELECT id FROM lockers_pricingtier WHERE size='Large' LIMIT 1")
large_tier = cursor.fetchone()

if not small_tier or not medium_tier or not large_tier:
    print("Creating pricing tiers...")
    cursor.execute("""
        INSERT INTO lockers_pricingtier (name, size, base_price, hourly_rate, daily_rate, weekly_rate, is_active)
        VALUES 
        ('Economy Small', 'Small', 0, 5.00, 30.00, 150.00, 1),
        ('Economy Medium', 'Medium', 0, 8.00, 50.00, 250.00, 1),
        ('Economy Large', 'Large', 0, 12.00, 80.00, 400.00, 1)
        ON DUPLICATE KEY UPDATE name=name
    """)
    conn.commit()
    
    cursor.execute("SELECT id FROM lockers_pricingtier WHERE size='Small' LIMIT 1")
    small_tier = cursor.fetchone()
    cursor.execute("SELECT id FROM lockers_pricingtier WHERE size='Medium' LIMIT 1")
    medium_tier = cursor.fetchone()
    cursor.execute("SELECT id FROM lockers_pricingtier WHERE size='Large' LIMIT 1")
    large_tier = cursor.fetchone()

small_tier_id = small_tier[0]
medium_tier_id = medium_tier[0]
large_tier_id = large_tier[0]

# Egyptian locations data
egypt_locations = [
    ("Cairo Airport Terminal 3", "Airport Road", "Cairo", "11776", "Egypt", 30.1219, 31.4056),
    ("Maadi City Center", "Corniche El Maadi", "Maadi", "11431", "Egypt", 29.9602, 31.2503),
    ("Zamalek Cultural District", "26th of July Street", "Zamalek", "11211", "Egypt", 30.0626, 31.2197),
    ("Heliopolis Square", "Al Ahram Street", "Heliopolis", "11341", "Egypt", 30.0877, 31.3272),
    ("Nasr City Mall District", "Abbas El Akkad Street", "Nasr City", "11765", "Egypt", 30.0544, 31.3406),
    ("6th October City Center", "Central Axis", "6th October", "12573", "Egypt", 29.9668, 30.9381),
    ("New Cairo Festival City", "Road 90", "New Cairo", "11835", "Egypt", 30.0283, 31.4190),
]

for loc_name, street, city, zip_code, country, lat, lng in egypt_locations:
    # Check if location already exists
    cursor.execute("SELECT id FROM lockers_lockerlocation WHERE name = %s", (loc_name,))
    existing = cursor.fetchone()
    
    if existing:
        print(f"  {loc_name} already exists")
        location_id = existing[0]
    else:
        # Create address
        cursor.execute("""
            INSERT INTO lockers_locationaddress (street_address, city, zip_code, country, latitude, longitude)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (street, city, zip_code, country, lat, lng))
        address_id = cursor.lastrowid
        
        # Create location
        cursor.execute("""
            INSERT INTO lockers_lockerlocation 
            (name, address_id, description, operating_hours_start, operating_hours_end, is_active, created_at, updated_at)
            VALUES (%s, %s, %s, '06:00:00', '23:00:00', 1, NOW(), NOW())
        """, (loc_name, address_id, f"Smart locker facility in {city}"))
        location_id = cursor.lastrowid
        print(f"  Created {loc_name}")
        
        # Add 15 lockers per location (5 of each size)
        locker_configs = [
            ('Small', small_tier_id, 5),
            ('Medium', medium_tier_id, 5),
            ('Large', large_tier_id, 5)
        ]
        
        unit_num = 1
        for size, tier_id, count in locker_configs:
            for i in range(count):
                cursor.execute("""
                    INSERT INTO lockers_lockerunit 
                    (location_id, tier_id, unit_number, size, status, qr_code, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, 'Available', %s, NOW(), NOW())
                """, (location_id, tier_id, f"{unit_num:03d}", size, f"QR-{loc_name[:10]}-{unit_num}"))
                unit_num += 1

conn.commit()

# Show final stats
cursor.execute('SELECT COUNT(*) FROM lockers_lockerlocation')
print(f'\nTotal locations: {cursor.fetchone()[0]}')

cursor.execute('SELECT COUNT(*) FROM lockers_lockerunit')
print(f'Total lockers: {cursor.fetchone()[0]}')

cursor.execute("SELECT COUNT(*) FROM lockers_lockerunit WHERE status='Available'")
print(f'Available lockers: {cursor.fetchone()[0]}')

cursor.execute("""
    SELECT l.name, COUNT(u.id) as locker_count
    FROM lockers_lockerlocation l
    LEFT JOIN lockers_lockerunit u ON l.id = u.location_id
    GROUP BY l.id, l.name
    ORDER BY l.name
""")
print('\nLockers per location:')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]} lockers')

conn.close()
print("\n✓ Done!")
