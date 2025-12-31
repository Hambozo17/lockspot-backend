"""
API Testing Script for LockSpot with MySQL
"""
import requests
import json
from datetime import datetime, timedelta
import mysql.connector

BASE_URL = "http://localhost:8000/api"

print("="*60)
print("TESTING LOCKSPOT API WITH MYSQL DATABASE")
print("="*60)

# Test Login
print("\n1. Testing Login...")
response = requests.post(f"{BASE_URL}/auth/login/", json={
    "email": "demo@lockspot.com",
    "password": "demo123"
})
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print("SUCCESS - Login works")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)[:200]}")
else:
    print(f"FAILED - {response.text[:200]}")

# Test Locations
print("\n2. Testing Get Locations...")
response = requests.get(f"{BASE_URL}/locations/")
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    count = data.get('count', len(data) if isinstance(data, list) else 0)
    print(f"SUCCESS - Found {count} locations")
else:
    print(f"FAILED - {response.text[:200]}")

# Test Lockers
print("\n3. Testing Get Lockers...")
response = requests.get(f"{BASE_URL}/lockers/")
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    if isinstance(data, dict) and 'results' in data:
        print(f"SUCCESS - Found {len(data['results'])} lockers")
    elif isinstance(data, list):
        print(f"SUCCESS - Found {len(data)} lockers")
else:
    print(f"FAILED - {response.text[:200]}")

# Test MySQL Connection
print("\n4. Testing MySQL Database...")
try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='Hambz',
        database='lockspot'
    )
    cursor = conn.cursor(dictionary=True)
    
    # Check data counts
    cursor.execute("SELECT COUNT(*) as count FROM auth_user")
    users = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM lockers_lockerlocation")
    locations = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM lockers_lockerunit")
    lockers = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM lockers_booking WHERE status = 'Active'")
    bookings = cursor.fetchone()['count']
    
    print(f"SUCCESS - MySQL connected")
    print(f"  Users: {users}")
    print(f"  Locations: {locations}")
    print(f"  Lockers: {lockers}")
    print(f"  Active Bookings: {bookings}")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"FAILED - {str(e)}")

print("\n" + "="*60)
print("TESTING COMPLETE")
print("="*60)
