"""
Seed sample data for LockSpot Admin Dashboard
Run with: python manage.py shell < seed_data.py
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lockspot_backend.settings')
django.setup()

from lockers.models import (
    User, LocationAddress, LockerLocation, PricingTier, LockerUnit,
    Discount, Booking, Payment
)
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

print("🌱 Seeding LockSpot Database...")

# Create Pricing Tiers
print("Creating pricing tiers...")
tiers = []
tier_data = [
    {'name': 'Standard', 'size': 'Small', 'base_price': 0, 'hourly_rate': 5, 'daily_rate': 35, 'weekly_rate': 200},
    {'name': 'Standard', 'size': 'Medium', 'base_price': 0, 'hourly_rate': 8, 'daily_rate': 55, 'weekly_rate': 320},
    {'name': 'Standard', 'size': 'Large', 'base_price': 0, 'hourly_rate': 12, 'daily_rate': 80, 'weekly_rate': 450},
    {'name': 'Premium', 'size': 'Small', 'base_price': 5, 'hourly_rate': 7, 'daily_rate': 45, 'weekly_rate': 260},
    {'name': 'Premium', 'size': 'Medium', 'base_price': 5, 'hourly_rate': 10, 'daily_rate': 70, 'weekly_rate': 400},
    {'name': 'Premium', 'size': 'Large', 'base_price': 5, 'hourly_rate': 15, 'daily_rate': 100, 'weekly_rate': 560},
]
for data in tier_data:
    tier, _ = PricingTier.objects.get_or_create(name=data['name'], size=data['size'], defaults=data)
    tiers.append(tier)
print(f"  ✓ Created {len(tier_data)} pricing tiers")

# Create Locations
print("Creating locations...")
locations_data = [
    {
        'address': {'street_address': 'King Fahd Road, Exit 5', 'city': 'Riyadh', 'country': 'Saudi Arabia', 'latitude': 24.7136, 'longitude': 46.6753},
        'location': {'name': 'Riyadh Mall', 'description': 'Premium locker station at Riyadh Mall near main entrance', 'operating_hours_start': '09:00', 'operating_hours_end': '23:00', 'contact_phone': '+966500000001'}
    },
    {
        'address': {'street_address': 'Tahlia Street', 'city': 'Jeddah', 'country': 'Saudi Arabia', 'latitude': 21.4858, 'longitude': 39.1925},
        'location': {'name': 'Jeddah Central Station', 'description': 'Convenient storage at Jeddah transportation hub', 'operating_hours_start': '06:00', 'operating_hours_end': '00:00', 'contact_phone': '+966500000002'}
    },
    {
        'address': {'street_address': 'KAFD District', 'city': 'Riyadh', 'country': 'Saudi Arabia', 'latitude': 24.7665, 'longitude': 46.6350},
        'location': {'name': 'KAFD Tower', 'description': 'Smart lockers at King Abdullah Financial District', 'operating_hours_start': '07:00', 'operating_hours_end': '22:00', 'contact_phone': '+966500000003'}
    },
    {
        'address': {'street_address': 'Boulevard Riyadh', 'city': 'Riyadh', 'country': 'Saudi Arabia', 'latitude': 24.6765, 'longitude': 46.6845},
        'location': {'name': 'Boulevard Lockers', 'description': 'Store your bags while enjoying Boulevard entertainment', 'operating_hours_start': '10:00', 'operating_hours_end': '01:00', 'contact_phone': '+966500000004'}
    },
    {
        'address': {'street_address': 'Red Sea Mall', 'city': 'Jeddah', 'country': 'Saudi Arabia', 'latitude': 21.6132, 'longitude': 39.1169},
        'location': {'name': 'Red Sea Mall', 'description': 'Premium storage at Red Sea Mall shopping center', 'operating_hours_start': '09:00', 'operating_hours_end': '23:00', 'contact_phone': '+966500000005'}
    },
]

locations = []
for data in locations_data:
    addr, _ = LocationAddress.objects.get_or_create(
        street_address=data['address']['street_address'],
        defaults=data['address']
    )
    loc, _ = LockerLocation.objects.get_or_create(
        name=data['location']['name'],
        defaults={**data['location'], 'address': addr}
    )
    locations.append(loc)
print(f"  ✓ Created {len(locations_data)} locations")

# Create Lockers
print("Creating locker units...")
locker_count = 0
sizes = ['Small', 'Medium', 'Large']
for location in locations:
    for i in range(1, 11):  # 10 lockers per location
        size = sizes[i % 3]
        tier = PricingTier.objects.filter(size=size, name='Standard').first()
        LockerUnit.objects.get_or_create(
            location=location,
            unit_number=f'{location.name[:2].upper()}{str(i).zfill(2)}',
            defaults={
                'size': size,
                'tier': tier,
                'status': 'Available' if i % 4 != 0 else 'Booked'
            }
        )
        locker_count += 1
print(f"  ✓ Created {locker_count} lockers")

# Create Demo User
print("Creating demo user...")
demo_user, _ = User.objects.get_or_create(
    email='demo@lockspot.com',
    defaults={
        'first_name': 'Demo',
        'last_name': 'User',
        'phone': '+966555000000',
        'user_type': 'Customer',
        'is_verified': True
    }
)
demo_user.set_password('demo123')
demo_user.save()

# Create more sample users
sample_users = [
    {'email': 'ahmed@example.com', 'first_name': 'Ahmed', 'last_name': 'Al-Rashid', 'phone': '+966555001001'},
    {'email': 'sara@example.com', 'first_name': 'Sara', 'last_name': 'Al-Qahtani', 'phone': '+966555001002'},
    {'email': 'mohammed@example.com', 'first_name': 'Mohammed', 'last_name': 'Al-Harbi', 'phone': '+966555001003'},
]
for data in sample_users:
    user, _ = User.objects.get_or_create(email=data['email'], defaults=data)
    user.set_password('password123')
    user.save()
print(f"  ✓ Created sample users")

# Create Discounts
print("Creating discount codes...")
now = timezone.now()
discounts_data = [
    {'code': 'WELCOME20', 'description': '20% off for new users', 'discount_type': 'Percentage', 'discount_value': 20, 'valid_from': now, 'valid_to': now + timedelta(days=90), 'max_uses': 100},
    {'code': 'SUMMER15', 'description': 'Summer special 15% off', 'discount_type': 'Percentage', 'discount_value': 15, 'valid_from': now, 'valid_to': now + timedelta(days=60)},
    {'code': 'FLAT50', 'description': 'Flat 50 SAR off', 'discount_type': 'FixedAmount', 'discount_value': 50, 'min_booking_amount': 100, 'valid_from': now, 'valid_to': now + timedelta(days=30)},
]
for data in discounts_data:
    Discount.objects.get_or_create(code=data['code'], defaults=data)
print(f"  ✓ Created {len(discounts_data)} discount codes")

# Create Sample Bookings
print("Creating sample bookings...")
booking_count = 0
users = User.objects.filter(user_type='Customer')[:3]
available_lockers = LockerUnit.objects.filter(status='Available')[:6]

for i, locker in enumerate(available_lockers):
    user = users[i % len(users)]
    start = now + timedelta(hours=i*2)
    end = start + timedelta(hours=4)
    
    booking, created = Booking.objects.get_or_create(
        user=user,
        locker=locker,
        start_time=start,
        defaults={
            'end_time': end,
            'subtotal_amount': Decimal('40.00'),
            'total_amount': Decimal('40.00'),
            'status': 'Confirmed' if i % 3 == 0 else 'Active' if i % 3 == 1 else 'Completed'
        }
    )
    if created:
        booking_count += 1
        # Create payment for completed bookings
        if booking.status == 'Completed':
            Payment.objects.get_or_create(
                booking=booking,
                defaults={
                    'amount': booking.total_amount,
                    'status': 'Success',
                    'transaction_reference': f'TXN-{booking.id}-{i}'
                }
            )
print(f"  ✓ Created {booking_count} bookings")

print("\n✅ Database seeding complete!")
print(f"""
Summary:
--------
- Pricing Tiers: {PricingTier.objects.count()}
- Locations: {LockerLocation.objects.count()}
- Lockers: {LockerUnit.objects.count()}
- Users: {User.objects.count()}
- Discounts: {Discount.objects.count()}
- Bookings: {Booking.objects.count()}

Admin Login:
  Email: admin@lockspot.com
  Password: admin123

Demo User:
  Email: demo@lockspot.com
  Password: demo123
""")
