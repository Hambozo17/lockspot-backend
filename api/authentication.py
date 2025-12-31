"""
JWT Authentication for Django REST Framework - 100% Raw SQL
"""

import jwt
from datetime import datetime, timedelta
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from db_utils import DatabaseConnection


class MockUser:
    """Mock User object for authentication"""
    def __init__(self, user_data):
        self.id = user_data['id']
        self.email = user_data['email']
        self.first_name = user_data.get('first_name', '')
        self.last_name = user_data.get('last_name', '')
        self.phone = user_data.get('phone', '')
        self.user_type = user_data.get('user_type', 'Customer')
        self.is_verified = bool(user_data.get('is_verified', 0))
        self.is_active = bool(user_data.get('is_active', 1))
        self.is_authenticated = True


class JWTAuthentication(BaseAuthentication):
    """JWT Token Authentication - Raw SQL"""
    
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return None
        
        try:
            prefix, token = auth_header.split(' ')
            if prefix.lower() != 'bearer':
                return None
        except ValueError:
            return None
        
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM]
            )
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token')
        
        # Get user from database using raw SQL
        try:
            with DatabaseConnection.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT id, email, first_name, last_name, phone, 
                           user_type, is_verified, is_active
                    FROM auth_user
                    WHERE id = %s
                """, (payload.get('user_id'),))
                user_data = cursor.fetchone()
                cursor.close()
                
                if not user_data:
                    raise AuthenticationFailed('User not found')
                
                if not user_data['is_active']:
                    raise AuthenticationFailed('User account is disabled')
                
                user = MockUser(user_data)
                return (user, token)
        except Exception as e:
            raise AuthenticationFailed(f'Authentication failed: {str(e)}')


def create_access_token(user_data):
    """Generate JWT token for user - accepts dict or object"""
    expiration = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    # Handle both dict and object
    if isinstance(user_data, dict):
        user_id = user_data.get('id')
        email = user_data.get('email')
        user_type = user_data.get('user_type', 'Customer')
    else:
        user_id = user_data.id
        email = user_data.email
        user_type = user_data.user_type
    
    payload = {
        'user_id': user_id,
        'email': email,
        'user_type': user_type,
        'exp': expiration,
        'iat': datetime.utcnow()
    }
    
    token = jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return token


def get_token_expiration_seconds():
    """Get token expiration in seconds"""
    return settings.JWT_EXPIRATION_HOURS * 3600
