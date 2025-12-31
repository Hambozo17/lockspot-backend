"""
Raw SQL Query Functions for LockSpot API
Replace ORM queries with raw SQL for better control and performance
"""

from typing import List, Dict, Optional  # type: ignore
from datetime import datetime, timedelta
from django.contrib.auth.hashers import make_password, check_password
import uuid

from .db_utils import DatabaseConnection, format_datetime, parse_datetime, dict_to_insert, dict_to_update  # type: ignore


# ==========================================
# USER QUERIES
# ==========================================

def create_user(email: str, password: str, first_name: str, last_name: str, phone: str, **kwargs) -> Dict:
    """Create new user with raw SQL"""
    user_data = {
        'email': email,
        'password': make_password(password),
        'first_name': first_name,
        'last_name': last_name,
        'phone': phone,
        'user_type': kwargs.get('user_type', 'Customer'),
        'is_verified': kwargs.get('is_verified', 0),
        'is_staff': kwargs.get('is_staff', 0),
        'is_superuser': kwargs.get('is_superuser', 0),
        'is_active': 1,
        'created_at': format_datetime(datetime.now()),
        'updated_at': format_datetime(datetime.now()),
    }
    
    query, params = dict_to_insert('auth_user', user_data)
    user_id = DatabaseConnection.execute_insert(query, params)
    
    # Return created user
    return get_user_by_id(user_id)


def get_user_by_email(email: str) -> Optional[Dict]:
    """Get user by email"""
    query = "SELECT * FROM auth_user WHERE email = ?"
    return DatabaseConnection.execute_query_one(query, (email,))


def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Get user by ID"""
    query = "SELECT * FROM auth_user WHERE id = ?"
    return DatabaseConnection.execute_query_one(query, (user_id,))


def verify_user_password(email: str, password: str) -> Optional[Dict]:
    """Verify user password and return user if valid"""
    user = get_user_by_email(email)
    if user and check_password(password, user['password']):
        return user
    return None


def update_user(user_id: int, **fields) -> int:
    """Update user fields"""
    fields['updated_at'] = format_datetime(datetime.now())
    query, params = dict_to_update('auth_user', fields, 'id = ?', (user_id,))
    return DatabaseConnection.execute_update(query, params)


# ==========================================
# LOCATION QUERIES
# ==========================================

def get_all_locations() -> List[Dict]:
    """Get all active locations with their details"""
    query = """
        SELECT 
            loc.id AS location_id,
            loc.name,
            loc.description,
            loc.image,
            loc.operating_hours_start,
            loc.operating_hours_end,
            loc.is_active,
            loc.contact_phone,
            addr.id AS address_id,
            addr.street_address,
            addr.city,
            addr.state,
            addr.zip_code,
            addr.country,
            addr.latitude,
            addr.longitude,
            (SELECT COUNT(*) FROM lockers_lockerunit WHERE location_id = loc.id AND status = 'Available') AS available_count,
            (SELECT COUNT(*) FROM lockers_lockerunit WHERE location_id = loc.id) AS total_lockers
        FROM lockers_lockerlocation loc
        INNER JOIN lockers_locationaddress addr ON loc.address_id = addr.id
        WHERE loc.is_active = 1
        ORDER BY loc.name
    """
    return DatabaseConnection.execute_query(query)


def get_location_by_id(location_id: int) -> Optional[Dict]:
    """Get location details by ID"""
    query = """
        SELECT 
            loc.id AS location_id,
            loc.name,
            loc.description,
            loc.image,
            loc.operating_hours_start,
            loc.operating_hours_end,
            loc.is_active,
            loc.contact_phone,
            addr.id AS address_id,
            addr.street_address,
            addr.city,
            addr.state,
            addr.zip_code,
            addr.country,
            addr.latitude,
            addr.longitude
        FROM lockers_lockerlocation loc
        INNER JOIN lockers_locationaddress addr ON loc.address_id = addr.id
        WHERE loc.id = ?
    """
    return DatabaseConnection.execute_query_one(query, (location_id,))


# ==========================================
# LOCKER QUERIES
# ==========================================

def get_available_lockers(location_id: int, size: Optional[str] = None) -> List[Dict]:
    """Get available lockers at a location"""
    query = """
        SELECT 
            l.id AS locker_id,
            l.unit_number,
            l.size,
            l.status,
            l.qr_code,
            pt.id AS tier_id,
            pt.name AS tier_name,
            pt.base_price,
            pt.hourly_rate,
            pt.daily_rate,
            pt.weekly_rate,
            pt.description AS tier_description
        FROM lockers_lockerunit l
        INNER JOIN lockers_pricingtier pt ON l.tier_id = pt.id
        WHERE l.location_id = ? 
          AND l.status = 'Available'
          AND pt.is_active = 1
    """
    params = [location_id]
    
    if size:
        query += " AND l.size = ?"
        params.append(size)  # type: ignore
    
    query += " ORDER BY l.unit_number"
    return DatabaseConnection.execute_query(query, tuple(params))


def update_locker_status(locker_id: int, new_status: str) -> int:
    """Update locker status"""
    query = "UPDATE lockers_lockerunit SET status = ?, updated_at = ? WHERE id = ?"
    return DatabaseConnection.execute_update(query, (new_status, format_datetime(datetime.now()), locker_id))


# ==========================================
# BOOKING QUERIES
# ==========================================

def create_booking(user_id: int, locker_id: int, start_time: datetime, end_time: datetime,
                   subtotal: float, discount_amount: float, total: float, **kwargs) -> Dict:
    """Create new booking"""
    booking_data = {
        'user_id': user_id,
        'locker_id': locker_id,
        'start_time': format_datetime(start_time),
        'end_time': format_datetime(end_time),
        'booking_type': kwargs.get('booking_type', 'Storage'),
        'subtotal_amount': subtotal,
        'discount_amount': discount_amount,
        'total_amount': total,
        'status': kwargs.get('status', 'Confirmed'),
        'discount_id': kwargs.get('discount_id'),
        'created_at': format_datetime(datetime.now()),
        'updated_at': format_datetime(datetime.now()),
    }
    
    query, params = dict_to_insert('lockers_booking', booking_data)
    booking_id = DatabaseConnection.execute_insert(query, params)
    
    # Update locker status to Booked
    update_locker_status(locker_id, 'Booked')
    
    return get_booking_by_id(booking_id)  # type: ignore


def get_booking_by_id(booking_id: int) -> Optional[Dict]:
    """Get booking details by ID"""
    query = """
        SELECT 
            b.id AS booking_id,
            b.user_id,
            b.locker_id,
            b.discount_id,
            b.start_time,
            b.end_time,
            b.booking_type,
            b.subtotal_amount,
            b.discount_amount,
            b.total_amount,
            b.status,
            b.cancellation_reason,
            b.created_at,
            b.updated_at,
            l.unit_number,
            l.size AS locker_size,
            l.qr_code,
            loc.id AS location_id,
            loc.name AS location_name,
            addr.street_address,
            addr.city,
            addr.latitude,
            addr.longitude,
            pt.hourly_rate,
            u.email AS user_email,
            u.first_name,
            u.last_name,
            u.phone AS user_phone
        FROM lockers_booking b
        INNER JOIN lockers_lockerunit l ON b.locker_id = l.id
        INNER JOIN lockers_lockerlocation loc ON l.location_id = loc.id
        INNER JOIN lockers_locationaddress addr ON loc.address_id = addr.id
        INNER JOIN lockers_pricingtier pt ON l.tier_id = pt.id
        INNER JOIN auth_user u ON b.user_id = u.id
        WHERE b.id = ?
    """
    return DatabaseConnection.execute_query_one(query, (booking_id,))


def get_user_bookings(user_id: int, booking_status: Optional[str] = None) -> List[Dict]:
    """Get user's bookings with optional status filter"""
    query = """
        SELECT 
            b.id AS booking_id,
            b.start_time,
            b.end_time,
            b.booking_type,
            b.subtotal_amount,
            b.discount_amount,
            b.total_amount,
            b.status,
            b.created_at,
            l.id AS locker_id,
            l.unit_number,
            l.size AS locker_size,
            l.qr_code,
            loc.id AS location_id,
            loc.name AS location_name,
            addr.street_address,
            addr.city,
            addr.latitude,
            addr.longitude
        FROM lockers_booking b
        INNER JOIN lockers_lockerunit l ON b.locker_id = l.id
        INNER JOIN lockers_lockerlocation loc ON l.location_id = loc.id
        INNER JOIN lockers_locationaddress addr ON loc.address_id = addr.id
        WHERE b.user_id = ?
    """
    params = [user_id]
    
    if booking_status:
        query += " AND b.status = ?"
        params.append(booking_status)  # type: ignore
    
    query += " ORDER BY b.created_at DESC"
    return DatabaseConnection.execute_query(query, tuple(params))


def update_booking_status(booking_id: int, new_status: str, **kwargs) -> int:
    """Update booking status"""
    update_data = {
        'status': new_status,
        'updated_at': format_datetime(datetime.now())
    }
    
    if 'cancellation_reason' in kwargs:
        update_data['cancellation_reason'] = kwargs['cancellation_reason']
    
    query, params = dict_to_update('lockers_booking', update_data, 'id = ?', (booking_id,))
    rows = DatabaseConnection.execute_update(query, params)
    
    # If cancelled/completed, update locker status
    if new_status in ['Cancelled', 'Completed', 'Expired']:
        booking = get_booking_by_id(booking_id)
        if booking:
            update_locker_status(booking['locker_id'], 'Available')
    
    return rows


# ==========================================
# PAYMENT QUERIES
# ==========================================

def create_payment(booking_id: int, amount: float, **kwargs) -> Dict:
    """Create payment record"""
    payment_data = {
        'booking_id': booking_id,
        'method_id': kwargs.get('method_id'),
        'amount': amount,
        'payment_date': format_datetime(datetime.now()),
        'transaction_reference': kwargs.get('transaction_reference', str(uuid.uuid4())),
        'status': kwargs.get('status', 'Success'),
        'processed_by': kwargs.get('processed_by', 'System'),
    }
    
    query, params = dict_to_insert('lockers_payment', payment_data)
    payment_id = DatabaseConnection.execute_insert(query, params)
    
    # Get and return created payment
    return DatabaseConnection.execute_query_one(
        "SELECT * FROM lockers_payment WHERE id = ?",
        (payment_id,)
    )


def get_payment_by_booking(booking_id: int) -> Optional[Dict]:
    """Get payment for a booking"""
    query = "SELECT * FROM lockers_payment WHERE booking_id = ?"
    return DatabaseConnection.execute_query_one(query, (booking_id,))


# ==========================================
# QR CODE QUERIES
# ==========================================

def generate_qr_code(booking_id: int, code_type: str, expires_at: datetime) -> Dict:
    """Generate QR access code for booking"""
    qr_data = {
        'booking_id': booking_id,
        'code': str(uuid.uuid4()),
        'code_type': code_type,
        'generated_at': format_datetime(datetime.now()),
        'expires_at': format_datetime(expires_at),
        'is_used': 0,
    }
    
    query, params = dict_to_insert('lockers_qraccesscode', qr_data)
    qr_id = DatabaseConnection.execute_insert(query, params)
    
    return DatabaseConnection.execute_query_one(
        "SELECT * FROM lockers_qraccesscode WHERE id = ?",
        (qr_id,)
    )


def get_qr_codes_by_booking(booking_id: int) -> List[Dict]:
    """Get all QR codes for a booking"""
    query = "SELECT * FROM lockers_qraccesscode WHERE booking_id = ? ORDER BY generated_at DESC"
    return DatabaseConnection.execute_query(query, (booking_id,))


def verify_qr_code(code: str) -> Optional[Dict]:
    """Verify QR code and mark as used"""
    qr = DatabaseConnection.execute_query_one(
        "SELECT * FROM lockers_qraccesscode WHERE code = ? AND is_used = 0",
        (code,)
    )
    
    if qr:
        # Check if expired
        expires_at = parse_datetime(qr['expires_at'])
        if expires_at and expires_at < datetime.now():
            return None
        
        # Mark as used
        DatabaseConnection.execute_update(
            "UPDATE lockers_qraccesscode SET is_used = 1, used_at = ? WHERE id = ?",
            (format_datetime(datetime.now()), qr['id'])
        )
    
    return qr


# ==========================================
# DISCOUNT QUERIES
# ==========================================

def get_discount_by_code(code: str) -> Optional[Dict]:
    """Get discount by code"""
    query = """
        SELECT * FROM lockers_discount 
        WHERE code = ? 
          AND is_active = 1 
          AND datetime('now') BETWEEN valid_from AND valid_to
    """
    return DatabaseConnection.execute_query_one(query, (code,))


def validate_discount(code: str, booking_amount: float) -> Optional[Dict]:
    """Validate discount code and calculate discount"""
    discount = get_discount_by_code(code)
    
    if not discount:
        return None
    
    # Check if max uses exceeded
    if discount['max_uses'] and discount['current_uses'] >= discount['max_uses']:
        return None
    
    # Check minimum booking amount
    if booking_amount < discount['min_booking_amount']:
        return None
    
    # Calculate discount amount
    if discount['discount_type'] == 'Percentage':
        discount_amount = booking_amount * (discount['discount_value'] / 100)
    else:  # FixedAmount
        discount_amount = discount['discount_value']
    
    # Apply max discount cap
    if discount['max_discount_amount']:
        discount_amount = min(discount_amount, discount['max_discount_amount'])
    
    discount['calculated_discount'] = discount_amount
    return discount


def increment_discount_usage(discount_id: int):
    """Increment discount usage count"""
    query = "UPDATE lockers_discount SET current_uses = current_uses + 1 WHERE id = ?"
    return DatabaseConnection.execute_update(query, (discount_id,))


# ==========================================
# REVIEW QUERIES
# ==========================================

def create_review(booking_id: int, rating: int, title=None, comment=None) -> Dict:
    """Create review for booking"""
    review_data = {
        'booking_id': booking_id,
        'rating': rating,
        'title': title,
        'comment': comment,
        'is_verified': 1,
        'created_at': format_datetime(datetime.now()),
        'updated_at': format_datetime(datetime.now()),
    }
    
    query, params = dict_to_insert('lockers_review', review_data)
    review_id = DatabaseConnection.execute_insert(query, params)
    
    return DatabaseConnection.execute_query_one(
        "SELECT * FROM lockers_review WHERE id = ?",
        (review_id,)
    )


def get_location_reviews(location_id: int, limit: int = 50) -> List[Dict]:
    """Get reviews for a location"""
    query = """
        SELECT 
            r.*,
            u.first_name,
            u.last_name,
            b.created_at AS booking_date
        FROM lockers_review r
        INNER JOIN lockers_booking b ON r.booking_id = b.id
        INNER JOIN auth_user u ON b.user_id = u.id
        INNER JOIN lockers_lockerunit l ON b.locker_id = l.id
        WHERE l.location_id = ?
        ORDER BY r.created_at DESC
        LIMIT ?
    """
    return DatabaseConnection.execute_query(query, (location_id, limit))


# ==========================================
# NOTIFICATION QUERIES
# ==========================================

def create_notification(user_id: int, title: str, message: str, notification_type: str, **kwargs) -> Dict:
    """Create notification for user"""
    notif_data = {
        'user_id': user_id,
        'title': title,
        'message': message,
        'notification_type': notification_type,
        'related_booking_id': kwargs.get('booking_id'),
        'is_read': 0,
        'created_at': format_datetime(datetime.now()),
    }
    
    query, params = dict_to_insert('lockers_notification', notif_data)
    notif_id = DatabaseConnection.execute_insert(query, params)
    
    return DatabaseConnection.execute_query_one(
        "SELECT * FROM lockers_notification WHERE id = ?",
        (notif_id,)
    )


def get_user_notifications(user_id: int, unread_only: bool = False) -> List[Dict]:
    """Get user notifications"""
    query = "SELECT * FROM lockers_notification WHERE user_id = ?"
    params = [user_id]
    
    if unread_only:
        query += " AND is_read = 0"
    
    query += " ORDER BY created_at DESC LIMIT 50"
    return DatabaseConnection.execute_query(query, tuple(params))


def mark_notification_read(notification_id: int) -> int:
    """Mark notification as read"""
    query = "UPDATE lockers_notification SET is_read = 1, read_at = ? WHERE id = ?"
    return DatabaseConnection.execute_update(query, (format_datetime(datetime.now()), notification_id))
