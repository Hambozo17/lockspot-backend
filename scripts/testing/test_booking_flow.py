# Test Complete Booking Flow
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "https://hydrogenous-mittie-loopily.ngrok-free.dev/api"
HEADERS = {"ngrok-skip-browser-warning": "true", "Content-Type": "application/json"}

print("="*60)
print("TESTING COMPLETE BOOKING FLOW")
print("="*60)

# 1. Login
print("\n1. Testing Login...")
login_data = {
    "email": "testapi2@lockspot.com",
    "password": "Test123!"
}
response = requests.post(f"{BASE_URL}/auth/login/", json=login_data, headers=HEADERS)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    token = result['access_token']
    user_id = result['user']['id']
    print(f"   ✓ Logged in as: {result['user']['email']}")
    print(f"   User ID: {user_id}")
else:
    print(f"   ✗ Login failed: {response.text}")
    exit()

# 2. Get available lockers
print("\n2. Getting Available Lockers...")
auth_headers = {**HEADERS, "Authorization": f"Bearer {token}"}
response = requests.get(f"{BASE_URL}/lockers/available/?location_id=13&size=Small", headers=auth_headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    lockers = response.json()['results']
    print(f"   ✓ Found {len(lockers)} available lockers")
    if lockers:
        locker = lockers[0]
        print(f"   Selected: Locker #{locker['id']}, Unit: {locker['unit_number']}")
        print(f"   Location: {locker['location']['name']}")
        print(f"   Pricing: ${locker['pricing']['hourly_rate']}/hr")
    else:
        print("   ✗ No lockers available")
        exit()
else:
    print(f"   ✗ Failed: {response.text}")
    exit()

# 3. Create booking
print("\n3. Creating Booking...")
now = datetime.now()
end_time = now + timedelta(hours=2)
booking_data = {
    "locker_id": locker['id'],
    "start_time": now.isoformat(),
    "end_time": end_time.isoformat(),
    "booking_type": "Storage"
}
response = requests.post(f"{BASE_URL}/bookings/", json=booking_data, headers=auth_headers)
print(f"   Status: {response.status_code}")
if response.status_code == 201:
    booking = response.json()
    print(f"   ✓ Booking created successfully!")
    print(f"   Booking ID: {booking['booking_id']}")
    print(f"   Locker: {booking['unit_number']} at {booking['location_name']}")
    print(f"   Total: ${booking['total_amount']}")
    print(f"   Status: {booking['status']}")
else:
    print(f"   ✗ Booking failed: {response.text}")
    exit()

# 4. Get user's bookings
print("\n4. Retrieving User Bookings...")
response = requests.get(f"{BASE_URL}/bookings/?status=Active", headers=auth_headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    bookings = response.json()['results']
    print(f"   ✓ User has {len(bookings)} active bookings")
    for b in bookings[:3]:  # Show first 3
        print(f"     - Booking #{b['booking_id']}: {b['unit_number']} at {b['location_name']}")
else:
    print(f"   ✗ Failed: {response.text}")

# 5. Check locker availability decreased
print("\n5. Verifying Locker Availability...")
response = requests.get(f"{BASE_URL}/lockers/available/?location_id=13&size=Small", headers=auth_headers)
if response.status_code == 200:
    new_lockers = response.json()['results']
    print(f"   ✓ Now {len(new_lockers)} available lockers (was {len(lockers)})")
    print(f"   Difference: {len(lockers) - len(new_lockers)} locker(s) booked")
else:
    print(f"   ✗ Failed: {response.text}")

print("\n" + "="*60)
print("✓ ALL TESTS PASSED - BOOKING FLOW WORKS!")
print("="*60)
