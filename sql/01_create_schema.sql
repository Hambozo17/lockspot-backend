-- ==========================================
-- LockSpot Database Schema - Database First Approach
-- SQLite Database with Raw SQL
-- ==========================================

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- ==========================================
-- 1. USERS TABLE (Custom User Authentication)
-- ==========================================

CREATE TABLE IF NOT EXISTS auth_user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    password VARCHAR(128) NOT NULL,
    last_login DATETIME,
    is_superuser BOOLEAN NOT NULL DEFAULT 0,
    email VARCHAR(254) NOT NULL UNIQUE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    phone VARCHAR(20) NOT NULL UNIQUE,
    user_type VARCHAR(10) NOT NULL DEFAULT 'Customer' CHECK(user_type IN ('Customer', 'Admin')),
    is_verified BOOLEAN NOT NULL DEFAULT 0,
    profile_image VARCHAR(100),
    is_staff BOOLEAN NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_email ON auth_user(email);
CREATE INDEX IF NOT EXISTS idx_user_phone ON auth_user(phone);
CREATE INDEX IF NOT EXISTS idx_user_type ON auth_user(user_type);
CREATE INDEX IF NOT EXISTS idx_user_created ON auth_user(created_at);


-- ==========================================
-- 2. LOCATION ADDRESS TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS lockers_locationaddress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    street_address VARCHAR(255) NOT NULL,
    city VARCHAR(50) NOT NULL,
    state VARCHAR(50),
    zip_code VARCHAR(10),
    country VARCHAR(50) NOT NULL DEFAULT 'Saudi Arabia',
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8)
);

CREATE INDEX IF NOT EXISTS idx_address_city ON lockers_locationaddress(city);
CREATE INDEX IF NOT EXISTS idx_address_coords ON lockers_locationaddress(latitude, longitude);


-- ==========================================
-- 3. LOCKER LOCATION TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS lockers_lockerlocation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    address_id INTEGER NOT NULL,
    description TEXT,
    image VARCHAR(100),
    operating_hours_start TIME NOT NULL DEFAULT '08:00:00',
    operating_hours_end TIME NOT NULL DEFAULT '22:00:00',
    is_active BOOLEAN NOT NULL DEFAULT 1,
    contact_phone VARCHAR(20),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (address_id) REFERENCES lockers_locationaddress(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_location_name ON lockers_lockerlocation(name);
CREATE INDEX IF NOT EXISTS idx_location_active ON lockers_lockerlocation(is_active);
CREATE INDEX IF NOT EXISTS idx_location_address ON lockers_lockerlocation(address_id);


-- ==========================================
-- 4. PRICING TIER TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS lockers_pricingtier (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL,
    size VARCHAR(10) NOT NULL CHECK(size IN ('Small', 'Medium', 'Large')),
    base_price DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    hourly_rate DECIMAL(10, 2) NOT NULL,
    daily_rate DECIMAL(10, 2) NOT NULL,
    weekly_rate DECIMAL(10, 2),
    description VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, size)
);

CREATE INDEX IF NOT EXISTS idx_pricing_size ON lockers_pricingtier(size);
CREATE INDEX IF NOT EXISTS idx_pricing_active ON lockers_pricingtier(is_active);


-- ==========================================
-- 5. LOCKER UNIT TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS lockers_lockerunit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location_id INTEGER NOT NULL,
    tier_id INTEGER NOT NULL,
    unit_number VARCHAR(10) NOT NULL,
    size VARCHAR(10) NOT NULL CHECK(size IN ('Small', 'Medium', 'Large')),
    status VARCHAR(15) NOT NULL DEFAULT 'Available' CHECK(status IN ('Available', 'Booked', 'Maintenance', 'OutOfService')),
    qr_code VARCHAR(255) UNIQUE,
    last_maintenance_date DATE,
    notes TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (location_id) REFERENCES lockers_lockerlocation(id) ON DELETE CASCADE,
    FOREIGN KEY (tier_id) REFERENCES lockers_pricingtier(id) ON DELETE RESTRICT,
    UNIQUE(location_id, unit_number)
);

CREATE INDEX IF NOT EXISTS idx_locker_location ON lockers_lockerunit(location_id);
CREATE INDEX IF NOT EXISTS idx_locker_status ON lockers_lockerunit(status);
CREATE INDEX IF NOT EXISTS idx_locker_size ON lockers_lockerunit(size);
CREATE INDEX IF NOT EXISTS idx_locker_qr ON lockers_lockerunit(qr_code);


-- ==========================================
-- 6. DISCOUNT TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS lockers_discount (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255),
    discount_type VARCHAR(15) NOT NULL CHECK(discount_type IN ('Percentage', 'FixedAmount')),
    discount_value DECIMAL(10, 2) NOT NULL,
    min_booking_amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    max_discount_amount DECIMAL(10, 2),
    valid_from DATETIME NOT NULL,
    valid_to DATETIME NOT NULL,
    max_uses INTEGER,
    current_uses INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_discount_code ON lockers_discount(code);
CREATE INDEX IF NOT EXISTS idx_discount_valid ON lockers_discount(valid_from, valid_to);
CREATE INDEX IF NOT EXISTS idx_discount_active ON lockers_discount(is_active);


-- ==========================================
-- 7. BOOKING TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS lockers_booking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    locker_id INTEGER NOT NULL,
    discount_id INTEGER,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    booking_type VARCHAR(10) NOT NULL DEFAULT 'Storage' CHECK(booking_type IN ('Storage', 'Delivery')),
    subtotal_amount DECIMAL(10, 2) NOT NULL,
    discount_amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(15) NOT NULL DEFAULT 'Pending' CHECK(status IN ('Pending', 'Confirmed', 'Active', 'Completed', 'Cancelled', 'Expired')),
    cancellation_reason TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE RESTRICT,
    FOREIGN KEY (locker_id) REFERENCES lockers_lockerunit(id) ON DELETE RESTRICT,
    FOREIGN KEY (discount_id) REFERENCES lockers_discount(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_booking_user ON lockers_booking(user_id);
CREATE INDEX IF NOT EXISTS idx_booking_locker ON lockers_booking(locker_id);
CREATE INDEX IF NOT EXISTS idx_booking_status ON lockers_booking(status);
CREATE INDEX IF NOT EXISTS idx_booking_dates ON lockers_booking(start_time, end_time);
CREATE INDEX IF NOT EXISTS idx_booking_created ON lockers_booking(created_at);


-- ==========================================
-- 8. PAYMENT METHOD TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS lockers_paymentmethod (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    method_type VARCHAR(15) NOT NULL CHECK(method_type IN ('Visa', 'Mastercard', 'MobileWallet', 'Cash')),
    card_last_four VARCHAR(4),
    card_holder_name VARCHAR(100),
    expiry_month INTEGER,
    expiry_year INTEGER,
    wallet_phone VARCHAR(20),
    is_default BOOLEAN NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_payment_method_user ON lockers_paymentmethod(user_id);
CREATE INDEX IF NOT EXISTS idx_payment_method_active ON lockers_paymentmethod(is_active);


-- ==========================================
-- 9. PAYMENT TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS lockers_payment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL UNIQUE,
    method_id INTEGER,
    amount DECIMAL(10, 2) NOT NULL,
    payment_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    transaction_reference VARCHAR(100) UNIQUE,
    status VARCHAR(15) NOT NULL DEFAULT 'Pending' CHECK(status IN ('Pending', 'Success', 'Failed', 'Refunded', 'PartialRefund')),
    failure_reason VARCHAR(255),
    refund_amount DECIMAL(10, 2),
    refund_date DATETIME,
    processed_by VARCHAR(50),
    FOREIGN KEY (booking_id) REFERENCES lockers_booking(id) ON DELETE RESTRICT,
    FOREIGN KEY (method_id) REFERENCES lockers_paymentmethod(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_payment_booking ON lockers_payment(booking_id);
CREATE INDEX IF NOT EXISTS idx_payment_status ON lockers_payment(status);
CREATE INDEX IF NOT EXISTS idx_payment_date ON lockers_payment(payment_date);
CREATE INDEX IF NOT EXISTS idx_payment_reference ON lockers_payment(transaction_reference);


-- ==========================================
-- 10. REVIEW TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS lockers_review (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL UNIQUE,
    rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
    title VARCHAR(100),
    comment TEXT,
    is_verified BOOLEAN NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES lockers_booking(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_review_booking ON lockers_review(booking_id);
CREATE INDEX IF NOT EXISTS idx_review_rating ON lockers_review(rating);
CREATE INDEX IF NOT EXISTS idx_review_created ON lockers_review(created_at);


-- ==========================================
-- 11. QR ACCESS CODE TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS lockers_qraccesscode (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL,
    code VARCHAR(255) NOT NULL UNIQUE,
    code_type VARCHAR(15) NOT NULL DEFAULT 'Unlock' CHECK(code_type IN ('Unlock', 'Lock', 'Emergency')),
    generated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    used_at DATETIME,
    is_used BOOLEAN NOT NULL DEFAULT 0,
    FOREIGN KEY (booking_id) REFERENCES lockers_booking(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_qr_booking ON lockers_qraccesscode(booking_id);
CREATE INDEX IF NOT EXISTS idx_qr_code ON lockers_qraccesscode(code);
CREATE INDEX IF NOT EXISTS idx_qr_expires ON lockers_qraccesscode(expires_at);


-- ==========================================
-- 12. NOTIFICATION TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS lockers_notification (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(15) NOT NULL CHECK(notification_type IN ('Booking', 'Payment', 'Reminder', 'Promo', 'System', 'Security')),
    related_booking_id INTEGER,
    is_read BOOLEAN NOT NULL DEFAULT 0,
    read_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE,
    FOREIGN KEY (related_booking_id) REFERENCES lockers_booking(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_notification_user ON lockers_notification(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_read ON lockers_notification(is_read);
CREATE INDEX IF NOT EXISTS idx_notification_type ON lockers_notification(notification_type);
CREATE INDEX IF NOT EXISTS idx_notification_created ON lockers_notification(created_at);


-- ==========================================
-- 13. AUDIT LOG TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS lockers_auditlog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action VARCHAR(100) NOT NULL,
    table_name VARCHAR(50),
    record_id INTEGER,
    old_values TEXT,  -- JSON stored as TEXT in SQLite
    new_values TEXT,  -- JSON stored as TEXT in SQLite
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_user ON lockers_auditlog(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_table ON lockers_auditlog(table_name);
CREATE INDEX IF NOT EXISTS idx_audit_action ON lockers_auditlog(action);
CREATE INDEX IF NOT EXISTS idx_audit_created ON lockers_auditlog(created_at);
