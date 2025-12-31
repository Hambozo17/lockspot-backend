import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Hambz',
    database='lockspot'
)

cursor = conn.cursor()

# Check if lockers have pricing tiers assigned
cursor.execute("""
    SELECT COUNT(*) as total,
           SUM(CASE WHEN tier_id IS NULL THEN 1 ELSE 0 END) as no_tier
    FROM lockers_lockerunit
""")
row = cursor.fetchone()
print(f"Lockers: {row[0]} total, {row[1]} without pricing tier")

cursor.execute("SELECT COUNT(*) FROM lockers_pricingtier")
print(f"Pricing tiers: {cursor.fetchone()[0]}")

# Check locker with tier join
cursor.execute("""
    SELECT l.id, l.unit_number, l.size, l.tier_id, p.id as pricing_id
    FROM lockers_lockerunit l
    LEFT JOIN lockers_pricingtier p ON l.tier_id = p.id
    WHERE l.location_id = 13 AND l.size = 'Small' AND l.status = 'Available'
    LIMIT 5
""")
print("\nSample lockers at location 13:")
for row in cursor.fetchall():
    print(f"  Locker ID: {row[0]}, Unit: {row[1]}, Size: {row[2]}, Tier ID: {row[3]}, Pricing ID: {row[4]}")

conn.close()
