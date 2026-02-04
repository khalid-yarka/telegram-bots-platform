import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

# Import from config.py
from config import config

class DatabaseConnection:
    """Database connection manager"""

    @contextmanager
    def get_connection(self):
        """Get database connection with context manager"""
        conn = None
        try:
            conn = mysql.connector.connect(**config.DB_CONFIG)
            yield conn
        except Error as e:
            logger.error(f"Database connection error: {str(e)}")
            raise
        finally:
            if conn and conn.is_connected():
                conn.close()

def get_db_connection():
    """Get a database connection"""
    return DatabaseConnection().get_connection()

def test_connection():
    """Test database connection"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            return result[0] == 1
    except Exception as e:
        logger.error(f"Database test failed: {str(e)}")
        return False

if __name__ == '__main__':
    if test_connection():
        print("✅ Database connection successful!")
    else:
        print("❌ Database connection failed!")