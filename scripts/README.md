# Backend Scripts

Utility scripts for database management, testing, and maintenance.

## 📁 Directory Structure

```
scripts/
├── database_setup/          # Initial database population
├── testing/                 # API and integration tests
└── maintenance/             # Database maintenance and fixes
```

---

## 🗄️ Database Setup

Scripts for populating initial data.

### `populate_egyptian_locations.py`
**Purpose:** Add 7 Egyptian locker locations with full inventory

**Usage:**
```bash
python scripts/database_setup/populate_egyptian_locations.py
```

**Locations Added:**
- Cairo Airport Terminal 3
- Maadi City Center
- Zamalek Cultural District
- Heliopolis Square
- Nasr City Mall District
- 6th October City Center
- New Cairo Festival City

**Each location gets:** 15 lockers (5 Small, 5 Medium, 5 Large)

---

### `populate_all_locations.py`
**Purpose:** Populate ALL locations with lockers (if they have 0 lockers)

**Usage:**
```bash
python scripts/database_setup/populate_all_locations.py
```

**Output:**
```
Found 13 locations
Adding 15 lockers to each location with 0 lockers...
✅ Added 15 lockers to 'Cairo Tahrir Square'
✅ Final count: 195 total lockers across 13 locations
```

---

## 🧪 Testing

Scripts for validating API functionality.

### `test_authentication.py`
**Purpose:** Test login and registration endpoints

**Tests:**
- User registration
- Login with JWT token
- Invalid credentials handling
- Legacy password hash support

**Usage:**
```bash
python scripts/testing/test_authentication.py
```

---

### `test_booking_flow.py`
**Purpose:** End-to-end booking flow test

**Tests:**
1. User login
2. Fetch available lockers
3. Create booking
4. Verify booking in database
5. Check locker status updated

**Usage:**
```bash
python scripts/testing/test_booking_flow.py
```

**Sample Output:**
```
✅ Login successful (token: eyJhbGc...)
✅ Found 14 available lockers at location 10
✅ Booking created: ID 15
✅ Locker 137 status: Booked
✅ Total amount: SAR 60.00
```

---

## 🔧 Maintenance

Scripts for database verification and fixes.

### `verify_bookings.py`
**Purpose:** Check booking data integrity

**Checks:**
- Total bookings count
- Active vs completed bookings
- Booking status consistency
- Payment records

**Usage:**
```bash
python scripts/maintenance/verify_bookings.py
```

---

### `verify_database.py`
**Purpose:** Comprehensive database health check

**Checks:**
- All table existence
- Row counts
- Foreign key relationships
- Data consistency

**Usage:**
```bash
python scripts/maintenance/verify_database.py
```

---

### `verify_lockers.py`
**Purpose:** Validate locker availability and status

**Checks:**
- Total lockers per location
- Available vs booked count
- Status field accuracy
- Orphaned bookings

**Usage:**
```bash
python scripts/maintenance/verify_lockers.py
```

**Sample Output:**
```
Location: Riyadh Mall
  Total: 15 lockers
  Available: 14
  Booked: 1
  ✅ All lockers accounted for
```

---

### `verify_pricing.py`
**Purpose:** Verify pricing tier correctness

**Checks:**
- Pricing tiers per location
- Rate consistency (hourly, daily, weekly)
- Size-based pricing

**Usage:**
```bash
python scripts/maintenance/verify_pricing.py
```

---

### `find_user_password.py`
**Purpose:** Look up user credentials (admin use only)

**Usage:**
```bash
python scripts/maintenance/find_user_password.py
```

**Prompts for:** Email or user ID
**Shows:** User details and password hash info

⚠️ **Security Note:** For admin/debugging only

---

### `reset_user_passwords.py`
**Purpose:** Bulk password reset for users with old hash formats

**Use Cases:**
- Migrate from MD5/SHA256 to pbkdf2
- Reset compromised accounts
- Fix authentication issues

**Usage:**
```bash
python scripts/maintenance/reset_user_passwords.py
```

**Default password:** `TempPass123!`

---

### `fix_location_lockers.py`
**Purpose:** Fix locker inventory issues for specific locations

**Usage:**
```bash
python scripts/maintenance/fix_location_lockers.py
```

**Fixes:**
- Missing lockers for locations
- Incorrect locker counts
- Duplicate unit numbers

---

## 📝 Script Development Guidelines

### Creating New Scripts

1. **Place in correct folder:**
   - Database population → `database_setup/`
   - Testing/validation → `testing/`
   - Fixes/maintenance → `maintenance/`

2. **Use proper naming:**
   - Verbs first: `verify_`, `populate_`, `test_`, `fix_`
   - Descriptive: `reset_user_passwords.py` not `reset.py`

3. **Include docstrings:**
   ```python
   """
   Script Name: verify_bookings.py
   Purpose: Validate booking data integrity
   Author: LockSpot Team
   Date: 2025-12-31
   """
   ```

4. **Add error handling:**
   ```python
   try:
       # Your code
   except Exception as e:
       print(f"❌ Error: {e}")
       sys.exit(1)
   ```

5. **Provide feedback:**
   ```python
   print("✅ Success message")
   print("⚠️ Warning message")
   print("❌ Error message")
   ```

---

## 🔗 Database Connection

All scripts use the same connection settings:

```python
import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Hambz',
    database='lockspot'
)
```

**Update credentials in each script before running.**

---

## ⚡ Quick Reference

| Task | Script |
|------|--------|
| Add Egyptian locations | `database_setup/populate_egyptian_locations.py` |
| Populate all locations | `database_setup/populate_all_locations.py` |
| Test API auth | `testing/test_authentication.py` |
| Test bookings | `testing/test_booking_flow.py` |
| Check database | `maintenance/verify_database.py` |
| Check lockers | `maintenance/verify_lockers.py` |
| Check bookings | `maintenance/verify_bookings.py` |
| Reset passwords | `maintenance/reset_user_passwords.py` |

---

**Need help?** Open an issue on GitHub or contact the maintainers.
