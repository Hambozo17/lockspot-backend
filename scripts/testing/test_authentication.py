import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lockspot_backend.settings')
django.setup()

import mysql.connector
from django.contrib.auth.hashers import check_password

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Hambz',
    database='lockspot'
)

cursor = conn.cursor(dictionary=True)

# Get recent users
cursor.execute('SELECT id, email, password, first_name FROM auth_user ORDER BY id DESC LIMIT 5')
users = cursor.fetchall()

print('Recent users:')
for u in users:
    print(f'  ID: {u["id"]}, Email: {u["email"]}, Name: {u["first_name"]}')
    print(f'    Password hash: {u["password"][:50]}...')
    
    # Test password verification
    test_password = "Test123!"
    is_valid = check_password(test_password, u["password"])
    print(f'    Test password "Test123!" valid: {is_valid}')
    print()

conn.close()
