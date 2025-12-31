-- ==========================================
-- LockSpot Database Views - Analytics & Reports
-- ==========================================

-- ==========================================
-- View: Active Bookings Summary
-- Shows all currently active bookings with full details
-- ==========================================

CREATE VIEW IF NOT EXISTS v_active_bookings AS
SELECT 
    b.id AS booking_id,
    b.status,
    b.start_time,
    b.end_time,
    b.total_amount,
    u.id AS user_id,
    u.email,
    u.first_name || ' ' || u.last_name AS user_full_name,
    u.phone AS user_phone,
    l.id AS locker_id,
    l.unit_number,
    l.size AS locker_size,
    l.status AS locker_status,
    loc.id AS location_id,
    loc.name AS location_name,
    addr.city,
    addr.street_address,
    pt.hourly_rate,
    ROUND((JULIANDAY(b.end_time) - JULIANDAY(b.start_time)) * 24, 2) AS duration_hours,
    b.created_at AS booking_created_at
FROM lockers_booking b
INNER JOIN auth_user u ON b.user_id = u.id
INNER JOIN lockers_lockerunit l ON b.locker_id = l.id
INNER JOIN lockers_lockerlocation loc ON l.location_id = loc.id
INNER JOIN lockers_locationaddress addr ON loc.address_id = addr.id
INNER JOIN lockers_pricingtier pt ON l.tier_id = pt.id
WHERE b.status IN ('Active', 'Confirmed')
ORDER BY b.start_time DESC;


-- ==========================================
-- View: Available Lockers by Location
-- Shows all available lockers with their details
-- ==========================================

CREATE VIEW IF NOT EXISTS v_available_lockers AS
SELECT 
    l.id AS locker_id,
    l.unit_number,
    l.size,
    l.status,
    loc.id AS location_id,
    loc.name AS location_name,
    loc.is_active AS location_active,
    addr.city,
    addr.street_address,
    addr.latitude,
    addr.longitude,
    pt.id AS tier_id,
    pt.name AS tier_name,
    pt.hourly_rate,
    pt.daily_rate,
    pt.weekly_rate,
    loc.operating_hours_start,
    loc.operating_hours_end
FROM lockers_lockerunit l
INNER JOIN lockers_lockerlocation loc ON l.location_id = loc.id
INNER JOIN lockers_locationaddress addr ON loc.address_id = addr.id
INNER JOIN lockers_pricingtier pt ON l.tier_id = pt.id
WHERE l.status = 'Available' 
  AND loc.is_active = 1
ORDER BY loc.name, l.unit_number;


-- ==========================================
-- View: Location Statistics
-- Aggregate statistics per location
-- ==========================================

CREATE VIEW IF NOT EXISTS v_location_stats AS
SELECT 
    loc.id AS location_id,
    loc.name AS location_name,
    addr.city,
    COUNT(DISTINCT l.id) AS total_lockers,
    SUM(CASE WHEN l.status = 'Available' THEN 1 ELSE 0 END) AS available_lockers,
    SUM(CASE WHEN l.status = 'Booked' THEN 1 ELSE 0 END) AS booked_lockers,
    SUM(CASE WHEN l.status = 'Maintenance' THEN 1 ELSE 0 END) AS maintenance_lockers,
    COUNT(DISTINCT b.id) AS total_bookings,
    ROUND(AVG(CASE WHEN r.rating IS NOT NULL THEN r.rating END), 2) AS avg_rating,
    COUNT(DISTINCT r.id) AS review_count,
    ROUND(SUM(CASE WHEN b.status = 'Completed' THEN b.total_amount ELSE 0 END), 2) AS total_revenue,
    loc.is_active AS location_active
FROM lockers_lockerlocation loc
INNER JOIN lockers_locationaddress addr ON loc.address_id = addr.id
LEFT JOIN lockers_lockerunit l ON loc.id = l.location_id
LEFT JOIN lockers_booking b ON l.id = b.locker_id
LEFT JOIN lockers_review r ON b.id = r.booking_id
GROUP BY loc.id, loc.name, addr.city, loc.is_active
ORDER BY loc.name;


-- ==========================================
-- View: User Booking History
-- Complete booking history with all details
-- ==========================================

CREATE VIEW IF NOT EXISTS v_user_booking_history AS
SELECT 
    b.id AS booking_id,
    b.user_id,
    u.email,
    u.first_name || ' ' || u.last_name AS user_full_name,
    l.id AS locker_id,
    l.unit_number,
    l.size AS locker_size,
    loc.name AS location_name,
    addr.city,
    b.start_time,
    b.end_time,
    b.status,
    b.subtotal_amount,
    b.discount_amount,
    b.total_amount,
    ROUND((JULIANDAY(b.end_time) - JULIANDAY(b.start_time)) * 24, 2) AS duration_hours,
    p.status AS payment_status,
    p.payment_date,
    p.transaction_reference,
    r.rating,
    r.comment AS review_comment,
    b.created_at AS booking_date
FROM lockers_booking b
INNER JOIN auth_user u ON b.user_id = u.id
INNER JOIN lockers_lockerunit l ON b.locker_id = l.id
INNER JOIN lockers_lockerlocation loc ON l.location_id = loc.id
INNER JOIN lockers_locationaddress addr ON loc.address_id = addr.id
LEFT JOIN lockers_payment p ON b.id = p.booking_id
LEFT JOIN lockers_review r ON b.id = r.booking_id
ORDER BY b.created_at DESC;


-- ==========================================
-- View: Revenue Report
-- Daily revenue summary
-- ==========================================

CREATE VIEW IF NOT EXISTS v_revenue_report AS
SELECT 
    DATE(b.created_at) AS booking_date,
    COUNT(DISTINCT b.id) AS total_bookings,
    COUNT(DISTINCT b.user_id) AS unique_customers,
    SUM(b.subtotal_amount) AS gross_revenue,
    SUM(b.discount_amount) AS total_discounts,
    SUM(b.total_amount) AS net_revenue,
    SUM(CASE WHEN b.status = 'Completed' THEN b.total_amount ELSE 0 END) AS completed_revenue,
    SUM(CASE WHEN b.status = 'Cancelled' THEN b.total_amount ELSE 0 END) AS cancelled_revenue,
    ROUND(AVG(b.total_amount), 2) AS avg_booking_value
FROM lockers_booking b
WHERE b.status NOT IN ('Pending')
GROUP BY DATE(b.created_at)
ORDER BY booking_date DESC;


-- ==========================================
-- View: Popular Locations
-- Locations ranked by booking frequency
-- ==========================================

CREATE VIEW IF NOT EXISTS v_popular_locations AS
SELECT 
    loc.id AS location_id,
    loc.name AS location_name,
    addr.city,
    addr.street_address,
    COUNT(DISTINCT b.id) AS total_bookings,
    COUNT(DISTINCT b.user_id) AS unique_customers,
    ROUND(AVG(CASE WHEN r.rating IS NOT NULL THEN r.rating END), 2) AS avg_rating,
    COUNT(DISTINCT r.id) AS review_count,
    ROUND(SUM(b.total_amount), 2) AS total_revenue,
    ROUND(AVG(b.total_amount), 2) AS avg_booking_value,
    SUM(CASE WHEN l.status = 'Available' THEN 1 ELSE 0 END) AS available_lockers,
    COUNT(DISTINCT l.id) AS total_lockers
FROM lockers_lockerlocation loc
INNER JOIN lockers_locationaddress addr ON loc.address_id = addr.id
LEFT JOIN lockers_lockerunit l ON loc.id = l.location_id
LEFT JOIN lockers_booking b ON l.id = b.locker_id
LEFT JOIN lockers_review r ON b.id = r.booking_id
WHERE loc.is_active = 1
GROUP BY loc.id, loc.name, addr.city, addr.street_address
ORDER BY total_bookings DESC, avg_rating DESC;


-- ==========================================
-- View: Customer Activity
-- Customer engagement metrics
-- ==========================================

CREATE VIEW IF NOT EXISTS v_customer_activity AS
SELECT 
    u.id AS user_id,
    u.email,
    u.first_name || ' ' || u.last_name AS full_name,
    u.phone,
    u.user_type,
    u.is_verified,
    u.created_at AS registration_date,
    COUNT(DISTINCT b.id) AS total_bookings,
    SUM(CASE WHEN b.status = 'Completed' THEN 1 ELSE 0 END) AS completed_bookings,
    SUM(CASE WHEN b.status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled_bookings,
    ROUND(SUM(b.total_amount), 2) AS total_spent,
    ROUND(AVG(b.total_amount), 2) AS avg_booking_value,
    MAX(b.created_at) AS last_booking_date,
    COUNT(DISTINCT r.id) AS reviews_given,
    ROUND(AVG(r.rating), 2) AS avg_rating_given,
    COUNT(DISTINCT pm.id) AS saved_payment_methods
FROM auth_user u
LEFT JOIN lockers_booking b ON u.id = b.user_id
LEFT JOIN lockers_review r ON b.id = r.booking_id
LEFT JOIN lockers_paymentmethod pm ON u.id = pm.user_id AND pm.is_active = 1
WHERE u.user_type = 'Customer'
GROUP BY u.id, u.email, u.first_name, u.last_name, u.phone, u.user_type, u.is_verified, u.created_at
ORDER BY total_bookings DESC, total_spent DESC;
