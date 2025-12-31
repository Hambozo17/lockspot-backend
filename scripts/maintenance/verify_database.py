import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Hambz',
    database='lockspot'
)

cursor = conn.cursor()

# Check locations and lockers
cursor.execute('SELECT COUNT(*) FROM lockers_lockerlocation')
print(f'Locations: {cursor.fetchone()[0]}')

cursor.execute('SELECT COUNT(*) FROM lockers_lockerunit')
print(f'Lockers: {cursor.fetchone()[0]}')

cursor.execute('SELECT id, name FROM lockers_lockerlocation LIMIT 10')
print('\nSample locations:')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]}')

cursor.execute("SELECT COUNT(*) FROM lockers_lockerunit WHERE status='Available'")
print(f'\nAvailable lockers: {cursor.fetchone()[0]}')

conn.close()
