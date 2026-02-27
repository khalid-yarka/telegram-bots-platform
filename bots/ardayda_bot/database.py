# bots/ardayda_bot/database.py

import mysql.connector as mysql
from mysql.connector import pooling
from datetime import datetime, timedelta
import pytz
import threading
from contextlib import contextmanager

# Set Somalia timezone
SOMALIA_TZ = pytz.timezone('Africa/Mogadishu')

# Connection pool configuration
DB_CONFIG = {
    'host': "Zabots1.mysql.pythonanywhere-services.com",
    'user': "Zabots1",
    'password': "users_db_pass",
    'database': "Zabots1$Ardayda",
    'charset': 'utf8mb4',
    'pool_name': 'ardayda_pool',
    'pool_size': 5,  # PythonAnywhere allows limited connections
    'pool_reset_session': True
}

# Global connection pool
connection_pool = None
pool_lock = threading.Lock()

# ---------- STATUS CONSTANTS ----------
STATUS_REG_NAME = "reg:name"
STATUS_REG_REGION = "reg:region"
STATUS_REG_SCHOOL = "reg:school"
STATUS_REG_CLASS = "reg:class"
STATUS_UPLOAD_WAIT_PDF = "upload:wait_pdf"
STATUS_UPLOAD_SUBJECT = "upload:subject"
STATUS_UPLOAD_TAGS = "upload:tags"
STATUS_SEARCH_SUBJECT = "search:subject"
STATUS_SEARCH_TAGS = "search:tags"
STATUS_SEARCH_RESULTS = "search:results"
STATUS_MENU_HOME = "menu:home"

# ================== CONNECTION POOL ==================

def init_connection_pool():
    """Initialize the connection pool (call once at startup)"""
    global connection_pool
    with pool_lock:
        if connection_pool is None:
            try:
                connection_pool = mysql.pooling.MySQLConnectionPool(**DB_CONFIG)
                print(f"✅ Connection pool initialized with size {DB_CONFIG['pool_size']}")
            except Exception as e:
                print(f"❌ Failed to create connection pool: {e}")
                # Fallback to non-pooled connections
                connection_pool = None

@contextmanager
def get_db_connection():
    """Get a connection from the pool with automatic cleanup"""
    conn = None
    cursor = None
    try:
        if connection_pool:
            conn = connection_pool.get_connection()
        else:
            # Fallback if pool not initialized
            conn = mysql.connect(**{k:v for k,v in DB_CONFIG.items() 
                                   if k not in ['pool_name', 'pool_size', 'pool_reset_session']})
        
        cursor = conn.cursor(dictionary=True)
        yield conn, cursor
        conn.commit()  # Auto-commit if no errors
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()  # Returns to pool if pooling is enabled

def somalia_now():
    """Get current time in Somalia"""
    return datetime.now(SOMALIA_TZ)

def utc_to_somalia(utc_dt):
    """Convert UTC datetime to Somalia time"""
    if utc_dt:
        return utc_dt + timedelta(hours=3)
    return utc_dt

# ================== USER FUNCTIONS ==================

def get_user(user_id):
    """Get user by ID - uses connection pool"""
    with get_db_connection() as (conn, cursor):
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        return cursor.fetchone()

def add_user(user_id):
    """Add new user"""
    with get_db_connection() as (conn, cursor):
        cursor.execute(
            "INSERT INTO users (user_id, status, created_at) VALUES (%s, %s, %s)",
            (user_id, STATUS_MENU_HOME, somalia_now())
        )

def get_user_status(user_id):
    """Get user status"""
    with get_db_connection() as (conn, cursor):
        cursor.execute("SELECT status FROM users WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        return result['status'] if result else None

def set_status(user_id, status):
    """Set user status"""
    with get_db_connection() as (conn, cursor):
        cursor.execute("UPDATE users SET status=%s WHERE user_id=%s", (status, user_id))

def set_user_name(user_id, name):
    with get_db_connection() as (conn, cursor):
        cursor.execute("UPDATE users SET name=%s WHERE user_id=%s", (name, user_id))

def set_user_region(user_id, region):
    with get_db_connection() as (conn, cursor):
        cursor.execute("UPDATE users SET region=%s WHERE user_id=%s", (region, user_id))

def set_user_school(user_id, school):
    with get_db_connection() as (conn, cursor):
        cursor.execute("UPDATE users SET school=%s WHERE user_id=%s", (school, user_id))

def set_user_class(user_id, user_class):
    with get_db_connection() as (conn, cursor):
        cursor.execute("UPDATE users SET class=%s WHERE user_id=%s", (user_class, user_id))

# ================== TEMPORARY DATA (Now using database only) ==================
def clear_search_temp(user_id):
    """Clear search temporary data"""
    with get_db_connection() as (conn, cursor):
        cursor.execute(
            "UPDATE users SET temp_subject=NULL, temp_tags=NULL WHERE user_id=%s",
            (user_id,)
        )

def save_upload_temp(user_id, pdf_file_id, pdf_unique_id, pdf_name):
    with get_db_connection() as (conn, cursor):
        cursor.execute(
            """UPDATE users SET 
               temp_pdf_file_id=%s, temp_pdf_unique_id=%s, temp_pdf_name=%s 
               WHERE user_id=%s""",
            (pdf_file_id, pdf_unique_id, pdf_name, user_id)
        )

def save_upload_subject(user_id, subject):
    with get_db_connection() as (conn, cursor):
        cursor.execute(
            "UPDATE users SET temp_subject=%s WHERE user_id=%s",
            (subject, user_id)
        )

def save_upload_tags(user_id, tags_string):
    with get_db_connection() as (conn, cursor):
        cursor.execute(
            "UPDATE users SET temp_tags=%s WHERE user_id=%s",
            (tags_string, user_id)
        )

def get_upload_temp(user_id):
    with get_db_connection() as (conn, cursor):
        cursor.execute(
            """SELECT temp_pdf_file_id, temp_pdf_unique_id, temp_pdf_name, 
                      temp_subject, temp_tags 
               FROM users WHERE user_id=%s""",
            (user_id,)
        )
        user = cursor.fetchone()
        
        if not user:
            return None
        
        tags = []
        if user.get("temp_tags"):
            tags = [t for t in user["temp_tags"].split(",") if t]
        
        return {
            "file_id": user.get("temp_pdf_file_id"),
            "unique_id": user.get("temp_pdf_unique_id"),
            "name": user.get("temp_pdf_name"),
            "subject": user.get("temp_subject"),
            "tags": tags
        }

def clear_upload_temp(user_id):
    with get_db_connection() as (conn, cursor):
        cursor.execute(
            """UPDATE users SET 
               temp_pdf_file_id=NULL, temp_pdf_unique_id=NULL, temp_pdf_name=NULL,
               temp_subject=NULL, temp_tags=NULL
               WHERE user_id=%s""",
            (user_id,)
        )

# ================== PDF FUNCTIONS ==================

def insert_pdf(file_id, name, subject, uploader_id, file_unique_id=None):
    """Insert PDF with transaction support"""
    with get_db_connection() as (conn, cursor):
        if not file_unique_id:
            file_unique_id = file_id
            
        cursor.execute(
            """INSERT INTO pdfs 
               (file_id, file_unique_id, name, subject, uploader_id, created_at) 
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (file_id, file_unique_id, name, subject, uploader_id, somalia_now())
        )
        return cursor.lastrowid

def pdf_exists(file_unique_id):
    if not file_unique_id:
        return False
    with get_db_connection() as (conn, cursor):
        cursor.execute("SELECT id FROM pdfs WHERE file_unique_id = %s", (file_unique_id,))
        return cursor.fetchone() is not None

def get_pdf_by_id(pdf_id):
    with get_db_connection() as (conn, cursor):
        cursor.execute("SELECT * FROM pdfs WHERE id=%s", (pdf_id,))
        return cursor.fetchone()

def get_user_pdfs_count(user_id):
    with get_db_connection() as (conn, cursor):
        cursor.execute("SELECT COUNT(*) as count FROM pdfs WHERE uploader_id=%s", (user_id,))
        result = cursor.fetchone()
        return result['count'] if result else 0

# ================== TAG FUNCTIONS ==================

def add_pdf_tag(pdf_id, tag):
    with get_db_connection() as (conn, cursor):
        cursor.execute(
            "INSERT INTO pdf_tags (pdf_id, tag) VALUES (%s, %s)", 
            (pdf_id, tag)
        )

def add_pdf_tags_bulk(pdf_id, tags):
    """Add multiple tags in one operation - more efficient"""
    if not tags:
        return
    with get_db_connection() as (conn, cursor):
        values = [(pdf_id, tag) for tag in tags]
        cursor.executemany(
            "INSERT INTO pdf_tags (pdf_id, tag) VALUES (%s, %s)",
            values
        )

def get_pdf_tags(pdf_id):
    with get_db_connection() as (conn, cursor):
        cursor.execute("SELECT tag FROM pdf_tags WHERE pdf_id=%s", (pdf_id,))
        return [row['tag'] for row in cursor.fetchall()]

# ================== SEARCH FUNCTIONS ==================

def search_pdfs(subject, tags=None):
    """Search PDFs by subject and tags"""
    if tags is None:
        tags = []
    
    with get_db_connection() as (conn, cursor):
        if tags:
            format_strings = ','.join(['%s'] * len(tags))
            query = f"""
            SELECT DISTINCT p.*
            FROM pdfs p
            LEFT JOIN pdf_tags t ON p.id = t.pdf_id
            WHERE p.subject = %s
            AND t.tag IN ({format_strings})
            ORDER BY p.created_at DESC
            """
            params = [subject] + tags
        else:
            query = """
            SELECT *
            FROM pdfs
            WHERE subject = %s
            ORDER BY created_at DESC
            """
            params = [subject]
        
        cursor.execute(query, params)
        return cursor.fetchall()

# ================== ADMIN FUNCTIONS ==================

def get_user_admin_status(user_id):
    with get_db_connection() as (conn, cursor):
        cursor.execute("SELECT is_admin FROM users WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        return result['is_admin'] if result else False

def set_user_admin(user_id, admin_status=True):
    with get_db_connection() as (conn, cursor):
        cursor.execute(
            "UPDATE users SET is_admin = %s WHERE user_id = %s",
            (admin_status, user_id)
        )
        return True

def get_user_suspended(user_id):
    with get_db_connection() as (conn, cursor):
        cursor.execute("SELECT suspended FROM users WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        return result['suspended'] if result else False

def set_user_suspended(user_id, suspended_status=True):
    with get_db_connection() as (conn, cursor):
        cursor.execute(
            "UPDATE users SET suspended = %s WHERE user_id = %s",
            (suspended_status, user_id)
        )
        return True

def log_admin_action(admin_id, action, target_type, target_id, details=""):
    with get_db_connection() as (conn, cursor):
        cursor.execute(
            """INSERT INTO ardayda_admin_logs 
               (admin_id, action, target_type, target_id, details, created_at) 
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (admin_id, action, target_type, target_id, details, somalia_now())
        )
        return True

def execute_sql_query(query, params=None):
    """Execute raw SQL query (ADMIN ONLY)"""
    with get_db_connection() as (conn, cursor):
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        # Try to fetch results if it's a SELECT
        try:
            return cursor.fetchall()
        except:
            # Not a SELECT query
            return None