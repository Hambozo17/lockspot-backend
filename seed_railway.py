import mysql.connector

conn = mysql.connector.connect(
    host='caboose.proxy.rlwy.net',
    port=32321,
    user='root',
    password='veFfWAZkZkjmNcPjAPCYESTJixGGZGrn',
    database='railway'
)
cursor = conn.cursor()
print('Connected to Railway MySQL!')

# 1. Create pricing tiers
print('Creating pricing tiers...')
cursor.execute('DELETE FROM lockers_pricingtier')
cursor.execute("""
    INSERT INTO lockers_pricingtier (name, size, base_price, hourly_rate, daily_rate, weekly_rate, is_active)
    VALUES 
    ('Economy Small', 'Small', 0, 5.00, 30.00, 150.00, 1),
    ('Economy Medium', 'Medium', 0, 8.00, 50.00, 250.00, 1),
    ('Economy Large', 'Large', 0, 12.00, 80.00, 400.00, 1)
""")
conn.commit()
print('Pricing tiers created!')

# Get tier IDs
cursor.execute("SELECT id FROM lockers_pricingtier WHERE size='Small' LIMIT 1")
small_tier_id = cursor.fetchone()[0]
cursor.execute("SELECT id FROM lockers_pricingtier WHERE size='Medium' LIMIT 1")
medium_tier_id = cursor.fetchone()[0]
cursor.execute("SELECT id FROM lockers_pricingtier WHERE size='Large' LIMIT 1")
large_tier_id = cursor.fetchone()[0]

# 2. Create Egyptian locations
locations = [
    ('Sheikh Zayed Mall', 'Arkan Plaza, 26th of July Corridor', 'Sheikh Zayed', 'Egypt', 30.0131, 30.9718),
    ('Cairo Festival City', 'Ring Road', 'New Cairo', 'Egypt', 30.0284, 31.4082),
    ('Alexandria Bibliotheca', 'Al Corniche Road, Shatby', 'Alexandria', 'Egypt', 31.2089, 29.9092),
    ('Citystars Heliopolis', 'Omar Ibn El Khattab Street', 'Heliopolis', 'Egypt', 30.0724, 31.3456),
    ('Mall of Egypt', '26th of July Corridor', '6th October', 'Egypt', 29.9726, 30.9433),
    ('Maadi Grand Mall', 'Corniche El Nile', 'Maadi', 'Egypt', 29.9602, 31.2569),
]

print('Creating locations...')
for name, street, city, country, lat, lng in locations:
    # Create address
    cursor.execute("""
        INSERT INTO lockers_locationaddress (street_address, city, zip_code, country, latitude, longitude)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (street, city, '12345', country, lat, lng))
    addr_id = cursor.lastrowid
    
    # Create location
    cursor.execute("""
        INSERT INTO lockers_lockerlocation 
        (name, address_id, description, operating_hours_start, operating_hours_end, is_active, created_at, updated_at)
        VALUES (%s, %s, %s, '06:00:00', '23:00:00', 1, NOW(), NOW())
    """, (name, addr_id, f'Smart locker facility at {name}, {city}'))
    loc_id = cursor.lastrowid
    print(f'  Created: {name}')
    
    # Create 15 lockers per location (5 of each size)
    prefix = ''.join([w[0].upper() for w in name.split()[:2]])
    unit = 1
    for size, tier_id in [('Small', small_tier_id), ('Medium', medium_tier_id), ('Large', large_tier_id)]:
        for i in range(5):
            cursor.execute("""
                INSERT INTO lockers_lockerunit 
                (location_id, tier_id, unit_number, size, status, qr_code, created_at, updated_at)
                VALUES (%s, %s, %s, %s, 'Available', %s, NOW(), NOW())
            """, (loc_id, tier_id, f'{prefix}-{unit:03d}', size, f'QR-{prefix}-{unit:03d}'))
            unit += 1

conn.commit()

# Summary
cursor.execute('SELECT COUNT(*) FROM lockers_lockerlocation')
print(f'Total locations: {cursor.fetchone()[0]}')
cursor.execute('SELECT COUNT(*) FROM lockers_lockerunit')
print(f'Total lockers: {cursor.fetchone()[0]}')
conn.close()
print('Done!')
