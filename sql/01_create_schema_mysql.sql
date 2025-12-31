-- ==========================================
-- LockSpot Database Schema - MySQL Version
-- Database First Approach
-- ==========================================

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS lockspot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE lockspot;

-- ==========================================
-- 1. USERS TABLE (Custom User Authentication)
-- ==========================================

CREATE TABLE IF NOT EXISTS auth_user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    password VARCHAR(128) NOT NULL,
    last_login DATETIME NULL,
    is_superuser TINYINT(1) NOT NULL DEFAULT 0,
    email VARCHAR(254) NOT NULL UNIQUE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    phone VARCHAR(20) NOT NULL UNIQUE,
    user_type VARCHAR(10) NOT NULL DEFAULT 'Customer' CHECK(user_type IN ('Customer', 'Admin')),
    is_verified TINYINT(1) NOT NULL DEFAULT 0,
    profile_image VARCHAR(100) NULL,
    is_staff TINYINT(1) NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_email (email),
    INDEX idx_user_phone (phone),
    INDEX idx_user_type (user_type),
    INDEX idx_user_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ==========================================
-- 2. LOCATION ADDRESS TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS lockers_locationaddress (
    id INT AUTO_INCREMENT PRIMARY KEY,
    street_address VARCHAR(255) NOT NULL,
    city VARCHAR(50) NOT NULL,
    state VARCHAR(50) NULL,
    zip_code VARCHAR(10) NULL,
    country VARCHAR(50) NOT NULL DEFAULT 'Saudi Arabia',
    latitude DECIMAL(10, 8) NULL,
    longitude DECIMAL(11, 8) NULL,
    INDEX idx_address_city (city),
    INDEX idx_address_coords (latitude, longitude)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ==========================================
-- 3. LOCKER LOCATION TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS lockers_lockerlocation (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    address_id INT NOT NULL,
    description TEXT NULL,
    image VARCHAR(100) NULL,
    operating_hours_start TIME NOT NULL DEFAULT '08:00:00',
    operating_hours_end TIME NOT NULL DEFAULT '22:00:00',
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    contact_phone VARCHAR(20) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_location_name (name),
    INDEX idx_location_active (is_active),
    INDEX idx_location_address (address_id),
    FOREIGN KEY (address_id) REFERENCES lockers_locationaddress(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ==========================================
-- 4. PRICING TIER TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS lockers_pricingtier (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    size VARCHAR(10) NOT NULL CHECK(size IN ('Small', 'Medium', 'Large')),
    base_price DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    hourly_rate DECIMAL(10, 2) NOT NULL,
    daily_rate DECIMAL(10, 2) NOT NULL,
    weekly_rate DECIMAL(10, 2) NULL,
    description VARCHAR(255) NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_name_size (name, size),
    INDEX idx_pricing_size (size),
    INDEX idx_pricing_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ==========================================
-- 5. LOCKER UNIT TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS lockers_lockerunit (
    id INT AUTO_INCREMENT PRIMARY KEY,
    location_id INT NOT NULL,
    tier_id INT NOT NULL,
    unit_number VARCHAR(10) NOT NULL,
    size VARCHAR(10) NOT NULL CHECK(size IN ('Small', 'Medium', 'Large')),
    status VARCHAR(15) NOT NULL DEFAULT 'Available' CHECK(status IN ('Available', 'Booked', 'Maintenance', 'OutOfService')),
    qr_code VARCHAR(255) UNIQUE NULL,
    last_maintenance_date DATE NULL,
    notes TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_location_unit (location_id, unit_number),
    INDEX idx_locker_location (location_id),
    INDEX idx_locker_status (status),
    INDEX idx_locker_size (size),
    INDEX idx_locker_qr (qr_code),
    FOREIGN KEY (location_id) REFERENCES lockers_lockerlocation(id) ON DELETE CASCADE,
    FOREIGN KEY (tier_id) REFERENCES lockers_pricingtier(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ==========================================
-- 6. DISCOUNT TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS lockers_discount (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255) NULL,
    discount_type VARCHAR(15) NOT NULL CHECK(discount_type IN ('Percentage', 'FixedAmount')),
    discount_value DECIMAL(10, 2) NOT NULL,
    min_booking_amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    max_discount_amount DECIMAL(10, 2) NULL,
    valid_from DATETIME NOT NULL,
    valid_to DATETIME NOT NULL,
    max_uses INT NULL,
    current_uses INT NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_discount_code (code),
    INDEX idx_discount_valid (valid_from, valid_to),
    INDEX idx_discount_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ==========================================
-- 7. BOOKING TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS lockers_booking (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    locker_id INT NOT NULL,
    discount_id INT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    booking_type VARCHAR(10) NOT NULL DEFAULT 'Storage' CHECK(booking_type IN ('Storage', 'Delivery')),
    subtotal_amount DECIMAL(10, 2) NOT NULL,
    discount_amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(15) NOT NULL DEFAULT 'Pending' CHECK(status IN ('Pending', 'Confirmed', 'Active', 'Completed', 'Cancelled', 'Expired')),
    cancellation_reason TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_booking_user (user_id),
    INDEX idx_booking_locker (locker_id),
    INDEX idx_booking_status (status),
    INDEX idx_booking_dates (start_time, end_time),
    INDEX idx_booking_created (created_at),
    FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE RESTRICT,
    FOREIGN KEY (locker_id) REFERENCES lockers_lockerunit(id) ON DELETE RESTRICT,
    FOREIGN KEY (discount_id) REFERENCES lockers_discount(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ==========================================
-- 8. PAYMENT METHOD TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS lockers_paymentmethod (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    method_type VARCHAR(15) NOT NULL CHECK(method_type IN ('Visa', 'Mastercard', 'MobileWallet', 'Cash')),
    card_last_four VARCHAR(4) NULL,
    card_holder_name VARCHAR(100) NULL,
    expiry_month INT NULL,
    expiry_year INT NULL,
    wallet_phone VARCHAR(20) NULL,
    is_default TINYINT(1) NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_payment_method_user (user_id),
    INDEX idx_payment_method_active (is_active),
    FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ==========================================
-- 9. PAYMENT TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS lockers_payment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL UNIQUE,
    method_id INT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    payment_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    transaction_reference VARCHAR(100) UNIQUE NULL,
    status VARCHAR(15) NOT NULL DEFAULT 'Pending' CHECK(status IN ('Pending', 'Success', 'Failed', 'Refunded', 'PartialRefund')),
    failure_reason VARCHAR(255) NULL,
    refund_amount DECIMAL(10, 2) NULL,
    refund_date DATETIME NULL,
    processed_by VARCHAR(50) NULL,
    INDEX idx_payment_booking (booking_id),
    INDEX idx_payment_status (status),
    INDEX idx_payment_date (payment_date),
    INDEX idx_payment_reference (transaction_reference),
    FOREIGN KEY (booking_id) REFERENCES lockers_booking(id) ON DELETE RESTRICT,
    FOREIGN KEY (method_id) REFERENCES lockers_paymentmethod(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ==========================================
-- 10. REVIEW TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS lockers_review (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL UNIQUE,
    rating INT NOT NULL CHECK(rating >= 1 AND rating <= 5),
    title VARCHAR(100) NULL,
    comment TEXT NULL,
    is_verified TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_review_booking (booking_id),
    INDEX idx_review_rating (rating),
    INDEX idx_review_created (created_at),
    FOREIGN KEY (booking_id) REFERENCES lockers_booking(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ==========================================
-- 11. QR ACCESS CODE TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS lockers_qraccesscode (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    code VARCHAR(255) NOT NULL UNIQUE,
    code_type VARCHAR(15) NOT NULL DEFAULT 'Unlock' CHECK(code_type IN ('Unlock', 'Lock', 'Emergency')),
    generated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    used_at DATETIME NULL,
    is_used TINYINT(1) NOT NULL DEFAULT 0,
    INDEX idx_qr_booking (booking_id),
    INDEX idx_qr_code (code),
    INDEX idx_qr_expires (expires_at),
    FOREIGN KEY (booking_id) REFERENCES lockers_booking(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ==========================================
-- 12. NOTIFICATION TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS lockers_notification (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(15) NOT NULL CHECK(notification_type IN ('Booking', 'Payment', 'Reminder', 'Promo', 'System', 'Security')),
    related_booking_id INT NULL,
    is_read TINYINT(1) NOT NULL DEFAULT 0,
    read_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_notification_user (user_id),
    INDEX idx_notification_read (is_read),
    INDEX idx_notification_type (notification_type),
    INDEX idx_notification_created (created_at),
    FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE,
    FOREIGN KEY (related_booking_id) REFERENCES lockers_booking(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ==========================================
-- 13. AUDIT LOG TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS lockers_auditlog (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    action VARCHAR(100) NOT NULL,
    table_name VARCHAR(50) NULL,
    record_id INT NULL,
    old_values JSON NULL,
    new_values JSON NULL,
    ip_address VARCHAR(45) NULL,
    user_agent VARCHAR(500) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_audit_user (user_id),
    INDEX idx_audit_table (table_name),
    INDEX idx_audit_action (action),
    INDEX idx_audit_created (created_at),
    FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
