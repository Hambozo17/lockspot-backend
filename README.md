# LockSpot Backend

Django REST API for the LockSpot smart locker booking system.

---

## Quick Start

### 1. Environment Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/macOS)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Configuration

Update `lockspot_backend/settings.py` with your MySQL credentials:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'lockspot',
        'USER': 'root',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

### 3. Initialize Database

```bash
# Apply migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Seed sample data (optional)
python scripts/seed_data.py
```

### 4. Run Server

```bash
python manage.py runserver
```

Server will be available at `http://localhost:8000`

---

## Project Structure

```
backend/
├── manage.py                 # Django CLI
├── requirements.txt          # Python dependencies
├── db_utils.py               # Database connection utilities
├── lockspot_backend/         # Django project settings
│   ├── settings.py           # Configuration
│   ├── urls.py               # Root URL routing
│   └── wsgi.py               # WSGI application
├── lockers/                  # Main application
│   ├── models.py             # Database models
│   ├── admin.py              # Admin panel configuration
│   └── migrations/           # Database migrations
├── api/                      # REST API
│   ├── views.py              # API endpoints
│   ├── serializers.py        # Data serialization
│   ├── urls.py               # API routing
│   └── authentication.py     # JWT authentication
├── scripts/                  # Utility scripts
│   ├── seed_data.py          # Populate sample data
│   ├── check_users.py        # View database users
│   └── test_*.py             # Test scripts
└── sql/                      # Raw SQL schemas
    ├── 01_create_schema.sql
    └── 01_create_schema_mysql.sql
```

---

## API Reference

### Authentication

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/auth/register/` | Register new user | No |
| `POST` | `/api/auth/login/` | Login and get token | No |
| `GET` | `/api/auth/me/` | Get current user | Yes |

#### Register

```bash
POST /api/auth/register/
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "securepassword",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+201234567890"
}
```

#### Login

```bash
POST /api/auth/login/
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "securepassword"
}
```

**Response:**
```json
{
    "access_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 86400,
    "user": {
        "id": 1,
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe"
    }
}
```

---

### Locations

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/api/locations/` | List all locations | No |
| `GET` | `/api/locations/{id}/` | Get location details | No |
| `GET` | `/api/locations/{id}/pricing/` | Get pricing tiers | No |
| `GET` | `/api/locations/{id}/lockers/` | Get lockers at location | No |

#### List Locations

```bash
GET /api/locations/
```

**Response:**
```json
{
    "count": 3,
    "results": [
        {
            "location_id": 1,
            "name": "Sheikh Zayed Mall",
            "description": "Premium smart lockers",
            "address": {
                "street_address": "Arkan Plaza",
                "city": "Sheikh Zayed",
                "country": "Egypt",
                "latitude": "30.0131",
                "longitude": "30.9718"
            },
            "available_lockers": 5,
            "total_lockers": 15
        }
    ]
}
```

---

### Lockers

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/api/lockers/` | List lockers | No |
| `GET` | `/api/lockers/available/` | List available lockers | No |
| `GET` | `/api/lockers/{id}/` | Get locker details | No |

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `location_id` | int | Filter by location |
| `size` | string | Filter by size (Small, Medium, Large) |
| `status` | string | Filter by status |

---

### Bookings

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/api/bookings/` | List user bookings | Yes |
| `POST` | `/api/bookings/` | Create new booking | Yes |
| `GET` | `/api/bookings/{id}/` | Get booking details | Yes |
| `POST` | `/api/bookings/{id}/cancel/` | Cancel booking | Yes |
| `GET` | `/api/bookings/{id}/qr_code/` | Get QR code | Yes |

#### Create Booking

```bash
POST /api/bookings/
Authorization: Bearer <token>
Content-Type: application/json

{
    "locker_id": 1,
    "start_time": "2025-01-01T10:00:00Z",
    "end_time": "2025-01-01T14:00:00Z",
    "booking_type": "Storage"
}
```

---

### Discounts

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/discounts/validate/` | Validate discount code | No |

---

## Admin Dashboard

Access the admin panel at `http://localhost:8000/admin/`

Features:
- Modern Jazzmin theme
- User management
- Location and locker management
- Booking oversight
- Payment tracking

---

## Database Models

### User
- `id`, `email`, `password`, `first_name`, `last_name`, `phone`
- `user_type`, `is_verified`, `is_active`

### LockerLocation
- `id`, `name`, `description`, `address_id`
- `operating_hours_start`, `operating_hours_end`

### LockerUnit
- `id`, `location_id`, `unit_number`, `size`, `status`
- `tier_id`, `is_active`

### Booking
- `id`, `user_id`, `locker_id`, `discount_id`
- `start_time`, `end_time`, `status`
- `subtotal_amount`, `discount_amount`, `total_amount`

### Payment
- `id`, `booking_id`, `method_id`, `amount`
- `status`, `transaction_reference`

---

## Environment Variables

Create a `.env` file in the backend directory:

```env
SECRET_KEY=your-secret-key
DEBUG=True
DB_NAME=lockspot
DB_USER=root
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=3306
JWT_SECRET=your-jwt-secret
```

---

## Scripts

| Script | Description |
|--------|-------------|
| `scripts/seed_data.py` | Populate database with sample data |
| `scripts/check_users.py` | View all users in database |
| `scripts/test_registration.py` | Test user registration |
| `scripts/test_mysql_connection.py` | Test database connection |

---

## Testing

```bash
# Run Django tests
python manage.py test

# Test API endpoints
python scripts/test_api_simple.py
```

---

## Deployment

### Using Gunicorn

```bash
pip install gunicorn
gunicorn lockspot_backend.wsgi:application --bind 0.0.0.0:8000
```

### Using ngrok (Development)

```bash
ngrok http 8000
```

Update `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` in settings.py with your ngrok URL.
