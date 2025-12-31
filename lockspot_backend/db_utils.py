"""
Database connection and raw SQL utilities for LockSpot
Using raw SQL queries instead of ORM for database operations
"""

import mysql.connector
from mysql.connector import Error
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from contextlib import contextmanager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# ==========================================
# Database Configuration - MySQL
# ==========================================

# MySQL Connection Configuration (from .env file)
DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'lockspot'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'port': int(os.getenv('DB_PORT', 3306)),
    'charset': 'utf8mb4',
    'autocommit': False,
}


class DatabaseConnection:
    """Manages database connections and raw SQL execution"""
    
    @staticmethod
    @contextmanager
    def get_connection():
        """
        Context manager for MySQL database connections
        Usage:
            with DatabaseConnection.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users")
        """
        conn = None
        try:
            conn = mysql.connector.connect(**DATABASE_CONFIG)
            yield conn
            conn.commit()
        except Error as e:
            if conn:
                conn.rollback()
            print(f"Database error: {e}")
            raise e
        finally:
            if conn and conn.is_connected():
                conn.close()
    
    @staticmethod
    def execute_query(query: str, params: Tuple = ()) -> List[Dict]:
        """
        Execute SELECT query and return results as list of dictionaries
        
        Args:
            query: SQL query string
            params: Query parameters tuple
            
        Returns:
            List of dictionaries representing rows
        """
        with DatabaseConnection.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()
            return results  # type: ignore
    
    @staticmethod
    def execute_query_one(query: str, params: Tuple = ()) -> Optional[Dict]:
        """
        Execute SELECT query and return single result as dictionary
        
        Args:
            query: SQL query string
            params: Query parameters tuple
            
        Returns:
            Dictionary representing single row or None
        """
        with DatabaseConnection.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params)
            row = cursor.fetchone()
            cursor.close()
            return row  # type: ignore
    
    @staticmethod
    def execute_insert(query: str, params: Tuple = ()) -> int:
        """
        Execute INSERT query and return the last inserted row ID
        
        Args:
            query: SQL query string
            params: Query parameters tuple
            
        Returns:
            Last inserted row ID
        """
        with DatabaseConnection.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            last_id = cursor.lastrowid
            cursor.close()
            return last_id
    
    @staticmethod
    def execute_update(query: str, params: Tuple = ()) -> int:
        """
        Execute UPDATE/DELETE query and return number of affected rows
        
        Args:
            query: SQL query string
            params: Query parameters tuple
            
        Returns:
            Number of affected rows
        """
        with DatabaseConnection.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows_affected = cursor.rowcount
            cursor.close()
            return rows_affected
    
    @staticmethod
    def execute_many(query: str, params_list: List[Tuple]) -> int:
        """
        Execute multiple queries with different parameters (bulk insert/update)
        
        Args:
            query: SQL query string
            params_list: List of parameter tuples
            
        Returns:
            Number of affected rows
        """
        with DatabaseConnection.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            rows_affected = cursor.rowcount
            cursor.close()
            return rows_affected
    
    @staticmethod
    def execute_script(script_path: str):
        """
        Execute SQL script file
        
        Args:
            script_path: Path to .sql file
        """
        with open(script_path, 'r', encoding='utf-8') as f:
            script = f.read()
        
        with DatabaseConnection.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # Split script into individual statements
                statements = []
                current_statement = []
                
                for line in script.split('\n'):
                    # Skip empty lines and comments
                    line = line.strip()
                    if not line or line.startswith('--'):
                        continue
                    
                    current_statement.append(line)
                    
                    # If line ends with semicolon, it's the end of a statement
                    if line.endswith(';'):
                        statement = ' '.join(current_statement)
                        if statement.strip():
                            statements.append(statement)
                        current_statement = []
                
                # Execute each statement
                for statement in statements:
                    if statement.strip():
                        cursor.execute(statement)
                
                conn.commit()
            finally:
                cursor.close()


# ==========================================
# Database Initialization
# ==========================================

def initialize_database():
    """
    Initialize database schema from SQL files
    Only creates tables/views if they don't exist (won't delete existing data)
    """
    sql_dir = os.path.join(os.path.dirname(__file__), 'sql')
    
    # Execute schema creation script (MySQL version)
    schema_file = os.path.join(sql_dir, '01_create_schema_mysql.sql')
    if os.path.exists(schema_file):
        print(f"Executing schema: {schema_file}")
        DatabaseConnection.execute_script(schema_file)
        print("✅ Database schema created/verified")
    
    # Execute views creation script (TODO: Convert to MySQL syntax)
    # views_file = os.path.join(sql_dir, '02_create_views.sql')
    # if os.path.exists(views_file):
    #     print(f"Executing views: {views_file}")
    #     DatabaseConnection.execute_script(views_file)
    #     print("✅ Database views created/verified")


# ==========================================
# Helper Functions for Common Queries
# ==========================================

def dict_to_insert(table_name: str, data: Dict) -> Tuple[str, Tuple]:
    """
    Convert dictionary to INSERT query
    
    Args:
        table_name: Table name
        data: Dictionary of column:value pairs
        
    Returns:
        Tuple of (query_string, params_tuple)
    """
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['?' for _ in data])
    query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
    return query, tuple(data.values())


def dict_to_update(table_name: str, data: Dict, where_clause: str, where_params: Tuple = ()) -> Tuple[str, Tuple]:
    """
    Convert dictionary to UPDATE query
    
    Args:
        table_name: Table name
        data: Dictionary of column:value pairs to update
        where_clause: WHERE condition (without WHERE keyword)
        where_params: Parameters for WHERE clause
        
    Returns:
        Tuple of (query_string, params_tuple)
    """
    set_clause = ', '.join([f"{key} = ?" for key in data.keys()])
    query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
    params = tuple(data.values()) + where_params
    return query, params


def format_datetime(dt: datetime):
    """Format datetime for SQLite"""
    return dt.strftime('%Y-%m-%d %H:%M:%S') if dt else None


def parse_datetime(dt_str: str) -> Optional[datetime]:
    """Parse datetime from SQLite"""
    if not dt_str:
        return None
    try:
        return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
    except:
        return None


# ==========================================
# Usage Example
# ==========================================

if __name__ == '__main__':
    # Initialize database from SQL files
    initialize_database()
    
    # Example: Insert user
    user_data = {
        'email': 'test@example.com',
        'first_name': 'Test',
        'last_name': 'User',
        'phone': '+966500000001',
        'password': 'hashed_password',
        'user_type': 'Customer',
        'is_verified': 1,
        'is_staff': 0,
        'is_superuser': 0,
        'is_active': 1,
        'created_at': format_datetime(datetime.now()),
        'updated_at': format_datetime(datetime.now()),
    }
    query, params = dict_to_insert('auth_user', user_data)
    # user_id = DatabaseConnection.execute_insert(query, params)
    # print(f"Inserted user with ID: {user_id}")
    
    # Example: Query users
    users = DatabaseConnection.execute_query(
        "SELECT id, email, first_name, last_name FROM auth_user WHERE user_type = ?",
        ('Customer',)
    )
    print(f"Found {len(users)} customers")
    
    # Example: Update user
    update_query, update_params = dict_to_update(
        'auth_user',
        {'is_verified': 1, 'updated_at': format_datetime(datetime.now())},
        'id = ?',
        (1,)
    )
    # rows_updated = DatabaseConnection.execute_update(update_query, update_params)
    # print(f"Updated {rows_updated} rows")
