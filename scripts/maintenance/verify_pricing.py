import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Hambz',
    database='lockspot'
)

cursor = conn.cursor()
cursor.execute("DESCRIBE lockers_pricingtier")
print("Pricing tier columns:")
for row in cursor.fetchall():
    print(f"  {row[0]} - {row[1]}")

conn.close()
