"""
API Views for LockSpot - 100% Raw SQL Implementation
No Django ORM - All queries use raw SQL
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from datetime import datetime, timedelta
import uuid
import hashlib
import json
from decimal import Decimal

# Import raw SQL functions
from db_utils import DatabaseConnection
from .authentication import create_access_token, get_token_expiration_seconds


# ==================== HELPER FUNCTIONS ====================

def dict_fetchall(cursor):
    """Return all rows from a cursor as a list of dicts"""
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def format_datetime(dt):
    """Format datetime for JSON response"""
    if dt is None:
        return None
    if isinstance(dt, str):
        return dt
    return dt.isoformat()


def parse_decimal(value):
    """Convert Decimal to float"""
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


# ==================== AUTH VIEWS ====================

class RegisterView(APIView):
    """User Registration with Raw SQL"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        phone = request.data.get('phone_number', '') or request.data.get('phone', '')
        
        if not email or not password:
            return Response(
                {'detail': 'Email and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Hash password
        from django.contrib.auth.hashers import make_password
        hashed_password = make_password(password)
        
        with DatabaseConnection.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Check if email exists
            cursor.execute("SELECT id FROM lockers_user WHERE email = %s", (email,))
            if cursor.fetchone():
                cursor.close()
                return Response(
                    {'detail': 'Email already exists'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create user
            cursor.execute("""
                INSERT INTO lockers_user 
                (email, password, first_name, last_name, phone, user_type, is_verified, 
                 is_staff, is_superuser, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, 'Customer', 0, 0, 0, 1, NOW(), NOW())
            """, (email, hashed_password, first_name, last_name, phone))
            
            user_id = cursor.lastrowid
            conn.commit()
            
            # Get created user
            cursor.execute("""
                SELECT id, email, first_name, last_name, phone, user_type, 
                       is_verified, created_at
                FROM lockers_user WHERE id = %s
            """, (user_id,))
            user = cursor.fetchone()
            cursor.close()
            
            # Generate token
            access_token = create_access_token(user)
            
            return Response({
                'user': {
                    'id': user['id'],
                    'email': user['email'],
                    'first_name': user['first_name'],
                    'last_name': user['last_name'],
                    'phone': user['phone'],
                    'user_type': user['user_type'],
                    'is_verified': bool(user['is_verified'])
                },
                'access_token': access_token,
                'token_type': 'Bearer',
                'expires_in': get_token_expiration_seconds()
            }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """User Login with Raw SQL"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {'detail': 'Email and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with DatabaseConnection.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT id, email, password, first_name, last_name, phone, 
                       user_type, is_verified, is_active
                FROM lockers_user WHERE email = %s
            """, (email,))
            
            user = cursor.fetchone()
            cursor.close()
            
            if not user:
                return Response(
                    {'detail': 'Invalid credentials'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            if not user['is_active']:
                return Response(
                    {'detail': 'Account is disabled'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Verify password
            from django.contrib.auth.hashers import check_password
            import hashlib
            
            password_valid = False
            
            # Check if it's a Django hash (starts with algorithm name)
            if user['password'].startswith('pbkdf2_'):
                password_valid = check_password(password, user['password'])
            # Check if it's an MD5 hash (32 characters, lowercase hex)
            elif len(user['password']) == 32 and all(c in '0123456789abcdef' for c in user['password']):
                # Legacy MD5 hash
                md5_hash = hashlib.md5(password.encode()).hexdigest()
                password_valid = (md5_hash == user['password'])
            # Check if it's a SHA256 hash (64 characters)
            elif len(user['password']) == 64 and all(c in '0123456789abcdef' for c in user['password']):
                # Legacy SHA256 hash
                sha256_hash = hashlib.sha256(password.encode()).hexdigest()
                password_valid = (sha256_hash == user['password'])
            
            if not password_valid:
                return Response(
                    {'detail': 'Invalid credentials'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Generate token
            access_token = create_access_token(user)
            
            return Response({
                'user': {
                    'id': user['id'],
                    'email': user['email'],
                    'first_name': user['first_name'],
                    'last_name': user['last_name'],
                    'phone': user['phone'],
                    'user_type': user['user_type'],
                    'is_verified': bool(user['is_verified'])
                },
                'access_token': access_token,
                'token_type': 'Bearer',
                'expires_in': get_token_expiration_seconds()
            })


class ProfileView(APIView):
    """User Profile with Raw SQL"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user profile"""
        user_id = request.user.id
        
        with DatabaseConnection.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT id, email, first_name, last_name, phone, user_type, 
                       is_verified, profile_image, created_at
                FROM lockers_user WHERE id = %s
            """, (user_id,))
            user = cursor.fetchone()
            cursor.close()
            
            if not user:
                return Response(
                    {'detail': 'User not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response({
                'id': user['id'],
                'email': user['email'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'phone': user['phone'],
                'user_type': user['user_type'],
                'is_verified': bool(user['is_verified']),
                'profile_image': user['profile_image'],
                'created_at': format_datetime(user['created_at'])
            })
    
    def patch(self, request):
        """Update user profile"""
        user_id = request.user.id
        
        # Build update query dynamically
        allowed_fields = ['first_name', 'last_name', 'phone', 'profile_image']
        updates = []
        params = []
        
        for field in allowed_fields:
            if field in request.data:
                updates.append(f"{field} = %s")
                params.append(request.data[field])
        
        if not updates:
            return Response(
                {'detail': 'No fields to update'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        params.append(user_id)
        
        with DatabaseConnection.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE lockers_user 
                SET {', '.join(updates)}, updated_at = NOW()
                WHERE id = %s
            """, params)
            conn.commit()
            cursor.close()
        
        # Return updated profile
        return self.get(request)


# ==================== LOCATION VIEWS ====================

class LocationListView(APIView):
    """List all locker locations with Raw SQL"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get all active locations"""
        with DatabaseConnection.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT 
                    l.id, l.name, l.description, l.image,
                    l.operating_hours_start, l.operating_hours_end,
                    l.contact_phone, l.is_active,
                    a.street_address, a.city, a.state, a.country,
                    a.latitude, a.longitude,
                    COUNT(DISTINCT lu.id) as total_lockers,
                    SUM(CASE WHEN lu.status = 'Available' THEN 1 ELSE 0 END) as available_lockers
                FROM lockers_lockerlocation l
                LEFT JOIN lockers_locationaddress a ON l.address_id = a.id
                LEFT JOIN lockers_lockerunit lu ON lu.location_id = l.id
                WHERE l.is_active = 1
                GROUP BY l.id
                ORDER BY l.name
            """)
            locations = cursor.fetchall()
            cursor.close()
            
            results = []
            for loc in locations:
                results.append({
                    'id': loc['id'],
                    'name': loc['name'],
                    'description': loc['description'],
                    'image': loc['image'],
                    'operating_hours': {
                        'start': str(loc['operating_hours_start']) if loc['operating_hours_start'] else '08:00:00',
                        'end': str(loc['operating_hours_end']) if loc['operating_hours_end'] else '22:00:00'
                    },
                    'contact_phone': loc['contact_phone'],
                    'address': {
                        'street': loc['street_address'],
                        'city': loc['city'],
                        'state': loc['state'],
                        'country': loc['country'],
                        'latitude': parse_decimal(loc['latitude']),
                        'longitude': parse_decimal(loc['longitude'])
                    },
                    'total_lockers': loc['total_lockers'] or 0,
                    'available_lockers': loc['available_lockers'] or 0,
                    'is_active': bool(loc['is_active'])
                })
            
            return Response({'results': results})


class LocationDetailView(APIView):
    """Get individual location details with Raw SQL"""
    permission_classes = [AllowAny]
    
    def get(self, request, location_id):
        """Get location by ID with locker counts by size"""
        with DatabaseConnection.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Get location details
            cursor.execute("""
                SELECT 
                    l.id, l.name, l.description, l.image,
                    l.operating_hours_start, l.operating_hours_end,
                    l.contact_phone, l.is_active,
                    a.street_address, a.city, a.state, a.country,
                    a.latitude, a.longitude
                FROM lockers_lockerlocation l
                LEFT JOIN lockers_locationaddress a ON l.address_id = a.id
                WHERE l.id = %s AND l.is_active = 1
            """, (location_id,))
            
            location = cursor.fetchone()
            
            if not location:
                cursor.close()
                return Response(
                    {'detail': 'Location not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get locker counts by size
            cursor.execute("""
                SELECT 
                    size,
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'Available' THEN 1 ELSE 0 END) as available
                FROM lockers_lockerunit
                WHERE location_id = %s
                GROUP BY size
            """, (location_id,))
            
            locker_counts = cursor.fetchall()
            
            # Get pricing
            cursor.execute("""
                SELECT DISTINCT
                    p.id, p.size, p.name, p.hourly_rate, p.daily_rate,
                    p.weekly_rate, p.is_active
                FROM lockers_pricingtier p
                JOIN lockers_lockerunit l ON l.tier_id = p.id
                WHERE l.location_id = %s AND p.is_active = 1
            """, (location_id,))
            
            pricing = cursor.fetchall()
            cursor.close()
            
            # Build response
            result = {
                'id': location['id'],
                'name': location['name'],
                'description': location['description'],
                'image': location['image'],
                'operating_hours': {
                    'start': str(location['operating_hours_start']) if location['operating_hours_start'] else '08:00:00',
                    'end': str(location['operating_hours_end']) if location['operating_hours_end'] else '22:00:00'
                },
                'contact_phone': location['contact_phone'],
                'address': {
                    'street': location['street_address'],
                    'city': location['city'],
                    'state': location['state'],
                    'country': location['country'],
                    'latitude': parse_decimal(location['latitude']),
                    'longitude': parse_decimal(location['longitude'])
                },
                'locker_counts': {},
                'pricing': []
            }
            
            # Add locker counts
            for count in locker_counts:
                result['locker_counts'][count['size']] = {
                    'total': count['total'],
                    'available': count['available']
                }
            
            # Add pricing
            for p in pricing:
                result['pricing'].append({
                    'id': p['id'],
                    'size': p['size'],
                    'name': p['name'],
                    'hourly_rate': parse_decimal(p['hourly_rate']),
                    'daily_rate': parse_decimal(p['daily_rate']),
                    'weekly_rate': parse_decimal(p['weekly_rate'])
                })
            
            return Response(result)


class LocationPricingView(APIView):
    """Get pricing for a specific location"""
    permission_classes = [AllowAny]
    
    def get(self, request, location_id):
        """Get all pricing tiers for a location"""
        with DatabaseConnection.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT DISTINCT
                    p.id, p.size, p.name, p.hourly_rate, p.daily_rate,
                    p.weekly_rate, p.description
                FROM lockers_pricingtier p
                JOIN lockers_lockerunit l ON l.tier_id = p.id
                WHERE l.location_id = %s AND p.is_active = 1
                ORDER BY p.size
            """, (location_id,))
            
            pricing = cursor.fetchall()
            cursor.close()
            
            results = []
            for p in pricing:
                results.append({
                    'id': p['id'],
                    'size': p['size'],
                    'name': p['name'],
                    'description': p['description'],
                    'hourly_rate': parse_decimal(p['hourly_rate']),
                    'daily_rate': parse_decimal(p['daily_rate']),
                    'weekly_rate': parse_decimal(p['weekly_rate'])
                })
            
            return Response({'results': results})


# ==================== LOCKER VIEWS ====================

class LockerListView(APIView):
    """List lockers with filters - Raw SQL"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get lockers with optional filters"""
        location_id = request.query_params.get('location_id')
        size = request.query_params.get('size')
        status_filter = request.query_params.get('status', 'Available')
        
        # Build query with conditions
        conditions = ["1=1"]
        params = []
        
        if location_id:
            conditions.append("l.location_id = %s")
            params.append(location_id)
        
        if size:
            conditions.append("l.size = %s")
            params.append(size)
        
        if status_filter:
            conditions.append("l.status = %s")
            params.append(status_filter)
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
            SELECT 
                l.id, l.unit_number, l.size, l.status,
                l.location_id, loc.name as location_name,
                p.hourly_rate, p.daily_rate, p.weekly_rate
            FROM lockers_lockerunit l
            JOIN lockers_lockerlocation loc ON l.location_id = loc.id
            JOIN lockers_pricingtier p ON l.tier_id = p.id
            WHERE {where_clause}
            ORDER BY loc.name, l.unit_number
        """
        
        with DatabaseConnection.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params)
            lockers = cursor.fetchall()
            cursor.close()
            
            results = []
            for locker in lockers:
                results.append({
                    'id': locker['id'],
                    'unit_number': locker['unit_number'],
                    'size': locker['size'],
                    'status': locker['status'],
                    'location': {
                        'id': locker['location_id'],
                        'name': locker['location_name']
                    },
                    'pricing': {
                        'hourly_rate': parse_decimal(locker['hourly_rate']),
                        'daily_rate': parse_decimal(locker['daily_rate']),
                        'weekly_rate': parse_decimal(locker['weekly_rate'])
                    }
                })
            
            return Response({'results': results})


class LockerAvailabilityView(APIView):
    """Check locker availability"""
    permission_classes = [AllowAny]
    
    def get(self, request, locker_id):
        """Check if a specific locker is available"""
        with DatabaseConnection.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT l.id, l.unit_number, l.size, l.status, 
                       loc.name as location_name
                FROM lockers_lockerunit l
                JOIN lockers_lockerlocation loc ON l.location_id = loc.id
                WHERE l.id = %s
            """, (locker_id,))
            
            locker = cursor.fetchone()
            cursor.close()
            
            if not locker:
                return Response(
                    {'detail': 'Locker not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response({
                'locker_id': locker['id'],
                'unit_number': locker['unit_number'],
                'size': locker['size'],
                'location_name': locker['location_name'],
                'is_available': locker['status'] == 'Available',
                'status': locker['status']
            })


# ==================== BOOKING VIEWS ====================

class BookingListCreateView(APIView):
    """List and Create Bookings with Raw SQL"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user's bookings with optional status filter"""
        user_id = request.user.id
        status_filter = request.query_params.get('status')
        
        # First, auto-complete expired bookings
        self._complete_expired_bookings(user_id)
        
        with DatabaseConnection.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            if status_filter:
                cursor.execute("""
                    SELECT b.id, b.user_id, b.locker_id, b.start_time, b.end_time,
                           b.booking_type, b.subtotal_amount, b.discount_amount, 
                           b.total_amount, b.status, b.created_at,
                           l.unit_number, l.size, loc.name as location_name
                    FROM lockers_booking b
                    JOIN lockers_lockerunit l ON b.locker_id = l.id
                    JOIN lockers_lockerlocation loc ON l.location_id = loc.id
                    WHERE b.user_id = %s AND b.status = %s
                    ORDER BY b.created_at DESC
                """, (user_id, status_filter))
            else:
                cursor.execute("""
                    SELECT b.id, b.user_id, b.locker_id, b.start_time, b.end_time,
                           b.booking_type, b.subtotal_amount, b.discount_amount, 
                           b.total_amount, b.status, b.created_at,
                           l.unit_number, l.size, loc.name as location_name
                    FROM lockers_booking b
                    JOIN lockers_lockerunit l ON b.locker_id = l.id
                    JOIN lockers_lockerlocation loc ON l.location_id = loc.id
                    WHERE b.user_id = %s
                    ORDER BY b.created_at DESC
                """, (user_id,))
            
            bookings = cursor.fetchall()
            cursor.close()
            
            results = []
            for b in bookings:
                results.append({
                    'booking_id': b['id'],
                    'user_id': b['user_id'],
                    'locker_id': b['locker_id'],
                    'location_name': b['location_name'],
                    'unit_number': b['unit_number'],
                    'size': b['size'],
                    'start_time': format_datetime(b['start_time']),
                    'end_time': format_datetime(b['end_time']),
                    'booking_type': b['booking_type'],
                    'subtotal_amount': parse_decimal(b['subtotal_amount']),
                    'discount_amount': parse_decimal(b['discount_amount']),
                    'total_amount': parse_decimal(b['total_amount']),
                    'status': b['status'],
                    'created_at': format_datetime(b['created_at']),
                    'qr_code': f"LOCKSPOT-{b['id']}",
                    'payment_status': 'paid'
                })
            
            return Response({'results': results})
    
    def _complete_expired_bookings(self, user_id):
        """Mark expired active bookings as completed"""
        with DatabaseConnection.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE lockers_booking 
                SET status = 'Completed', updated_at = NOW()
                WHERE user_id = %s 
                AND status IN ('Active', 'Confirmed')
                AND end_time < NOW()
            """, (user_id,))
            
            # Also free up the lockers
            cursor.execute("""
                UPDATE lockers_lockerunit l
                JOIN lockers_booking b ON l.id = b.locker_id
                SET l.status = 'Available'
                WHERE b.user_id = %s 
                AND b.status = 'Completed'
                AND l.status = 'Booked'
            """, (user_id,))
            
            conn.commit()
            cursor.close()
    
    def post(self, request):
        """Create a new booking"""
        user_id = request.user.id
        locker_id = request.data.get('locker_id')
        start_time = request.data.get('start_time')
        end_time = request.data.get('end_time')
        booking_type = request.data.get('booking_type', 'Storage')
        
        if not locker_id or not start_time or not end_time:
            return Response(
                {'detail': 'locker_id, start_time, and end_time are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with DatabaseConnection.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Get locker details and pricing
            cursor.execute("""
                SELECT l.id, l.unit_number, l.size, l.status, l.location_id,
                       p.hourly_rate, p.daily_rate, loc.name as location_name
                FROM lockers_lockerunit l
                JOIN lockers_pricingtier p ON l.tier_id = p.id
                JOIN lockers_lockerlocation loc ON l.location_id = loc.id
                WHERE l.id = %s
            """, (locker_id,))
            
            locker = cursor.fetchone()
            if not locker:
                cursor.close()
                return Response(
                    {'detail': 'Locker not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            if locker['status'] != 'Available':
                cursor.close()
                return Response(
                    {'detail': 'Locker not available'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Calculate pricing
            from datetime import datetime as dt
            start_dt = dt.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = dt.fromisoformat(end_time.replace('Z', '+00:00'))
            duration_hours = (end_dt - start_dt).total_seconds() / 3600
            
            if duration_hours <= 24:
                total_amount = parse_decimal(locker['hourly_rate']) * duration_hours
            else:
                total_amount = parse_decimal(locker['daily_rate']) * (duration_hours / 24)
            
            # Convert to MySQL format
            start_time_mysql = start_dt.strftime('%Y-%m-%d %H:%M:%S')
            end_time_mysql = end_dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Create booking
            cursor.execute("""
                INSERT INTO lockers_booking 
                (user_id, locker_id, start_time, end_time, booking_type,
                 subtotal_amount, discount_amount, total_amount, status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, 0, %s, 'Active', NOW(), NOW())
            """, (user_id, locker_id, start_time_mysql, end_time_mysql, booking_type, total_amount, total_amount))
            
            booking_id = cursor.lastrowid
            
            # Update locker status
            cursor.execute("""
                UPDATE lockers_lockerunit SET status = 'Booked' WHERE id = %s
            """, (locker_id,))
            
            conn.commit()
            cursor.close()
            
            return Response({
                'booking_id': booking_id,
                'user_id': user_id,
                'locker_id': locker_id,
                'location_name': locker['location_name'],
                'unit_number': locker['unit_number'],
                'size': locker['size'],
                'start_time': start_time,
                'end_time': end_time,
                'booking_type': booking_type,
                'subtotal_amount': total_amount,
                'discount_amount': 0,
                'total_amount': total_amount,
                'status': 'Active',
                'qr_code': f'LOCKSPOT-{booking_id}',
                'payment_status': 'paid'
            }, status=status.HTTP_201_CREATED)


class BookingDetailView(APIView):
    """Get individual booking details with Raw SQL"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, booking_id):
        """Get a single booking by ID"""
        user_id = request.user.id
        
        with DatabaseConnection.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT b.id, b.user_id, b.locker_id, b.start_time, b.end_time,
                       b.booking_type, b.subtotal_amount, b.discount_amount, 
                       b.total_amount, b.status, b.created_at,
                       l.unit_number, l.size, loc.name as location_name
                FROM lockers_booking b
                JOIN lockers_lockerunit l ON b.locker_id = l.id
                JOIN lockers_lockerlocation loc ON l.location_id = loc.id
                WHERE b.id = %s AND b.user_id = %s
            """, (booking_id, user_id))
            
            booking = cursor.fetchone()
            cursor.close()
            
            if not booking:
                return Response(
                    {'detail': 'Booking not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response({
                'booking_id': booking['id'],
                'user_id': booking['user_id'],
                'locker_id': booking['locker_id'],
                'location_name': booking['location_name'],
                'unit_number': booking['unit_number'],
                'size': booking['size'],
                'start_time': format_datetime(booking['start_time']),
                'end_time': format_datetime(booking['end_time']),
                'booking_type': booking['booking_type'],
                'subtotal_amount': parse_decimal(booking['subtotal_amount']),
                'discount_amount': parse_decimal(booking['discount_amount']),
                'total_amount': parse_decimal(booking['total_amount']),
                'status': booking['status'],
                'created_at': format_datetime(booking['created_at']),
                'qr_code': f'LOCKSPOT-{booking["id"]}',
                'payment_status': 'paid'
            })


class BookingQRView(APIView):
    """Generate QR code for a booking"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, booking_id):
        """Get QR code data for a booking"""
        user_id = request.user.id
        
        with DatabaseConnection.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT b.id, b.status, b.end_time,
                       l.unit_number, loc.name as location_name
                FROM lockers_booking b
                JOIN lockers_lockerunit l ON b.locker_id = l.id
                JOIN lockers_lockerlocation loc ON l.location_id = loc.id
                WHERE b.id = %s AND b.user_id = %s
            """, (booking_id, user_id))
            
            booking = cursor.fetchone()
            cursor.close()
            
            if not booking:
                return Response(
                    {'detail': 'Booking not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            qr_data = f'LOCKSPOT-{booking_id}'
            
            return Response({
                'booking_id': booking_id,
                'qr_code': qr_data,
                'qr_data': qr_data,
                'location_name': booking['location_name'],
                'unit_number': booking['unit_number'],
                'status': booking['status'],
                'expires_at': format_datetime(booking['end_time'])
            })


class BookingCancelView(APIView):
    """Cancel a booking"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, booking_id):
        """Cancel a booking by ID"""
        user_id = request.user.id
        
        with DatabaseConnection.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT id, locker_id, status FROM lockers_booking 
                WHERE id = %s AND user_id = %s
            """, (booking_id, user_id))
            
            booking = cursor.fetchone()
            
            if not booking:
                cursor.close()
                return Response(
                    {'detail': 'Booking not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            if booking['status'] in ['Cancelled', 'Completed']:
                cursor.close()
                return Response(
                    {'detail': f'Booking already {booking["status"].lower()}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            cursor.execute("""
                UPDATE lockers_booking 
                SET status = 'Cancelled', updated_at = NOW()
                WHERE id = %s
            """, (booking_id,))
            
            cursor.execute("""
                UPDATE lockers_lockerunit 
                SET status = 'Available'
                WHERE id = %s
            """, (booking['locker_id'],))
            
            conn.commit()
            cursor.close()
            
            return Response({
                'booking_id': booking_id,
                'status': 'Cancelled',
                'message': 'Booking cancelled successfully'
            })


# ==================== DISCOUNT VIEWS ====================

class DiscountView(APIView):
    """Validate discount codes with Raw SQL"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        code = request.data.get('code')
        
        if not code:
            return Response(
                {'detail': 'Discount code is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with DatabaseConnection.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT id, code, discount_type, discount_value, 
                       max_discount_amount, min_order_amount, max_uses,
                       current_uses, valid_from, valid_until, is_active
                FROM lockers_discount
                WHERE code = %s AND is_active = 1
            """, (code,))
            
            discount = cursor.fetchone()
            cursor.close()
            
            if not discount:
                return Response(
                    {'detail': 'Discount code not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check validity
            now = timezone.now()
            valid_from = discount['valid_from']
            valid_until = discount['valid_until']
            
            if valid_from and valid_from > now:
                return Response(
                    {'detail': 'Discount code not yet valid'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if valid_until and valid_until < now:
                return Response(
                    {'detail': 'Discount code has expired'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if discount['max_uses'] and discount['current_uses'] >= discount['max_uses']:
                return Response(
                    {'detail': 'Discount code usage limit reached'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response({
                'id': discount['id'],
                'code': discount['code'],
                'discount_type': discount['discount_type'],
                'discount_value': parse_decimal(discount['discount_value']),
                'max_discount_amount': parse_decimal(discount['max_discount_amount']),
                'min_order_amount': parse_decimal(discount['min_order_amount']),
                'valid': True
            })


# ==================== REVIEW VIEWS ====================

class ReviewListCreateView(APIView):
    """List and create reviews with Raw SQL"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get reviews - user's own or for a specific location"""
        user_id = request.user.id
        location_id = request.query_params.get('location_id')
        
        with DatabaseConnection.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            if location_id:
                cursor.execute("""
                    SELECT r.id, r.rating, r.title, r.comment, r.created_at,
                           u.first_name, u.last_name, u.email,
                           b.id as booking_id
                    FROM lockers_review r
                    JOIN lockers_user u ON r.user_id = u.id
                    JOIN lockers_booking b ON r.booking_id = b.id
                    JOIN lockers_lockerunit l ON b.locker_id = l.id
                    WHERE l.location_id = %s
                    ORDER BY r.created_at DESC
                """, (location_id,))
            else:
                cursor.execute("""
                    SELECT r.id, r.rating, r.title, r.comment, r.created_at,
                           b.id as booking_id,
                           l.unit_number, loc.name as location_name
                    FROM lockers_review r
                    JOIN lockers_booking b ON r.booking_id = b.id
                    JOIN lockers_lockerunit l ON b.locker_id = l.id
                    JOIN lockers_lockerlocation loc ON l.location_id = loc.id
                    WHERE r.user_id = %s
                    ORDER BY r.created_at DESC
                """, (user_id,))
            
            reviews = cursor.fetchall()
            cursor.close()
            
            results = []
            for r in reviews:
                review_data = {
                    'id': r['id'],
                    'rating': parse_decimal(r['rating']),
                    'title': r['title'],
                    'comment': r['comment'],
                    'created_at': format_datetime(r['created_at']),
                    'booking_id': r['booking_id']
                }
                
                if location_id:
                    review_data['user_name'] = f"{r['first_name']} {r['last_name']}"
                else:
                    review_data['location_name'] = r['location_name']
                    review_data['unit_number'] = r['unit_number']
                
                results.append(review_data)
            
            return Response({'results': results})
    
    def post(self, request):
        """Create a new review"""
        user_id = request.user.id
        booking_id = request.data.get('booking_id')
        rating = request.data.get('rating')
        title = request.data.get('title', '')
        comment = request.data.get('comment', '')
        
        if not booking_id or not rating:
            return Response(
                {'detail': 'booking_id and rating are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with DatabaseConnection.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Check booking exists and belongs to user
            cursor.execute("""
                SELECT id, status FROM lockers_booking
                WHERE id = %s AND user_id = %s
            """, (booking_id, user_id))
            
            booking = cursor.fetchone()
            
            if not booking:
                cursor.close()
                return Response(
                    {'detail': 'Booking not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            if booking['status'] != 'Completed':
                cursor.close()
                return Response(
                    {'detail': 'Can only review completed bookings'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if review already exists
            cursor.execute("""
                SELECT id FROM lockers_review WHERE booking_id = %s
            """, (booking_id,))
            
            if cursor.fetchone():
                cursor.close()
                return Response(
                    {'detail': 'Review already exists for this booking'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create review
            cursor.execute("""
                INSERT INTO lockers_review
                (user_id, booking_id, rating, title, comment, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            """, (user_id, booking_id, rating, title, comment))
            
            review_id = cursor.lastrowid
            conn.commit()
            cursor.close()
            
            return Response({
                'id': review_id,
                'booking_id': booking_id,
                'rating': float(rating),
                'title': title,
                'comment': comment,
                'message': 'Review created successfully'
            }, status=status.HTTP_201_CREATED)


class LocationReviewsView(APIView):
    """Get reviews for a specific location"""
    permission_classes = [AllowAny]
    
    def get(self, request, location_id):
        """Get all reviews for a location"""
        with DatabaseConnection.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT r.id, r.rating, r.title, r.comment, r.created_at,
                       u.first_name, u.last_name
                FROM lockers_review r
                JOIN lockers_user u ON r.user_id = u.id
                JOIN lockers_booking b ON r.booking_id = b.id
                JOIN lockers_lockerunit l ON b.locker_id = l.id
                WHERE l.location_id = %s
                ORDER BY r.created_at DESC
            """, (location_id,))
            
            reviews = cursor.fetchall()
            cursor.close()
            
            results = []
            for r in reviews:
                results.append({
                    'review_id': r['id'],
                    'rating': parse_decimal(r['rating']),
                    'title': r['title'],
                    'comment': r['comment'],
                    'created_at': format_datetime(r['created_at']),
                    'user_name': f"{r['first_name']} {r['last_name']}"
                })
            
            return Response({'results': results})


# ==================== NOTIFICATION VIEWS ====================

class NotificationListView(APIView):
    """User notifications with Raw SQL"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user's notifications"""
        user_id = request.user.id
        
        with DatabaseConnection.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT id, title, message, notification_type, is_read,
                       read_at, created_at, related_booking_id
                FROM lockers_notification
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 50
            """, (user_id,))
            
            notifications = cursor.fetchall()
            cursor.close()
            
            results = []
            for n in notifications:
                results.append({
                    'id': n['id'],
                    'title': n['title'],
                    'message': n['message'],
                    'notification_type': n['notification_type'],
                    'is_read': bool(n['is_read']),
                    'read_at': format_datetime(n['read_at']),
                    'created_at': format_datetime(n['created_at']),
                    'related_booking_id': n['related_booking_id']
                })
            
            return Response({'results': results})


class NotificationMarkReadView(APIView):
    """Mark notification as read"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, notification_id):
        """Mark a single notification as read"""
        user_id = request.user.id
        
        with DatabaseConnection.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE lockers_notification
                SET is_read = 1, read_at = NOW()
                WHERE id = %s AND user_id = %s
            """, (notification_id, user_id))
            conn.commit()
            
            if cursor.rowcount == 0:
                cursor.close()
                return Response(
                    {'detail': 'Notification not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            cursor.close()
            
            return Response({'status': 'read', 'message': 'Notification marked as read'})


class NotificationMarkAllReadView(APIView):
    """Mark all notifications as read"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Mark all user notifications as read"""
        user_id = request.user.id
        
        with DatabaseConnection.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE lockers_notification
                SET is_read = 1, read_at = NOW()
                WHERE user_id = %s AND is_read = 0
            """, (user_id,))
            count = cursor.rowcount
            conn.commit()
            cursor.close()
            
            return Response({
                'status': 'success',
                'message': f'{count} notifications marked as read',
                'count': count
            })


# ==================== HEALTH CHECK ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """API Health Check"""
    return Response({
        'status': 'online',
        'service': 'LockSpot API',
        'version': '3.0.0',
        'database': 'MySQL 8.0',
        'implementation': '100% Raw SQL - No ORM',
        'framework': 'Django REST Framework'
    })
