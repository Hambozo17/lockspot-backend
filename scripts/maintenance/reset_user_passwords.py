import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lockspot_backend.settings')
django.setup()

import mysql.connector
from django.contrib.auth.hashers import make_password

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Hambz',
    database='lockspot'
)

cursor = conn.cursor(dictionary=True)

# Find users with old hash formats (not starting with pbkdf2_)
cursor.execute("""
    SELECT id, email, password, first_name, last_name
    FROM auth_user 
    WHERE password NOT LIKE 'pbkdf2_%'
    ORDER BY id DESC
""")

old_hash_users = cursor.fetchall()

print(f"Found {len(old_hash_users)} users with old password hashes:\n")

for user in old_hash_users:
    print(f"ID: {user['id']}, Email: {user['email']}, Name: {user['first_name']} {user['last_name']}")
    hash_type = 'MD5' if len(user['password']) == 32 else 'SHA256' if len(user['password']) == 64 else 'Unknown'
    print(f"  Current hash type: {hash_type} ({len(user['password'])} chars)")
    print()

print("\n" + "="*60)
print("SOLUTION:")
print("="*60)
print("\nOption 1: Reset passwords to 'TempPass123!' for these users")
print("Option 2: Contact users to re-register with new passwords")
print("\nDo you want to reset passwords to 'TempPass123!'? (yes/no)")

response = input().strip().lower()

if response == 'yes':
    new_password = 'TempPass123!'
    hashed_password = make_password(new_password)
    
    for user in old_hash_users:
        cursor.execute("""
            UPDATE auth_user 
            SET password = %s, updated_at = NOW()
            WHERE id = %s
        """, (hashed_password, user['id']))
        print(f"✓ Reset password for {user['email']}")
    
    conn.commit()
    print(f"\n✓ Updated {len(old_hash_users)} users")
    print(f"New password for all: {new_password}")
    print("\nUsers should change their password after logging in!")
else:
    print("\nNo changes made.")

conn.close()
