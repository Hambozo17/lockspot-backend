"""
Test MySQL database connection
"""
from db_utils import DatabaseConnection

print('Testing MySQL connection...')
try:
    with DatabaseConnection.get_connection() as conn:
        print('✅ Connected to MySQL successfully!')
        print(f'Connection info: MySQL at localhost:3306')
        
        # Test a simple query
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT DATABASE() as current_db, VERSION() as version")
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            print(f'Current database: {result["current_db"]}')
            print(f'MySQL version: {result["version"]}')
        
        print('\n✅ All tests passed! MySQL is ready to use.')
except Exception as e:
    print(f'❌ Connection failed: {e}')
    print('\nPlease check:')
    print('1. MySQL service is running')
    print('2. Password is correct in db_utils.py')
    print('3. MySQL is accessible on localhost:3306')
