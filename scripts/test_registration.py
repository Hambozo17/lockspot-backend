"""Test user registration with MySQL"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api"

print("Testing User Registration with MySQL...")
print("="*60)

# Test new user registration
test_email = f"testuser_{int(datetime.now().timestamp())}@test.com"
registration_data = {
    "email": test_email,
    "password": "TestPass123!",
    "first_name": "Test",
    "last_name": "User",
    "phone_number": "+966500123456"
}

print(f"\n1. Registering new user: {test_email}")
response = requests.post(f"{BASE_URL}/auth/register/", json=registration_data)
print(f"Status: {response.status_code}")

if response.status_code == 201:
    print("SUCCESS - User registered!")
    data = response.json()
    print(f"User ID: {data.get('user', {}).get('id')}")
    print(f"Email: {data.get('user', {}).get('email')}")
    print(f"Token: {data.get('access_token', '')[:30]}...")
    
    # Verify in database
    print("\n2. Verifying in MySQL database...")
    import mysql.connector
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='Hambz',
        database='lockspot'
    )
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, email, first_name, last_name, phone FROM auth_user WHERE email = %s", (test_email,))
    user = cursor.fetchone()
    
    if user:
        print("SUCCESS - User found in MySQL!")
        print(f"  ID: {user['id']}")
        print(f"  Email: {user['email']}")
        print(f"  Name: {user['first_name']} {user['last_name']}")
        print(f"  Phone: {user['phone']}")
    else:
        print("ERROR - User NOT found in MySQL!")
    
    cursor.close()
    conn.close()
    
else:
    print(f"FAILED - Status {response.status_code}")
    print(f"Error: {response.text}")

print("\n" + "="*60)
print("Test complete!")
