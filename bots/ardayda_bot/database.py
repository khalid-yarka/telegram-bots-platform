# bots/ardayda_bot/database.py

import mysql.connector as mysql
#from master_db.connection import get_db_connection as get_connectio
from datetime import datetime

# ---------- STATUS CONSTANTS ----------
# Registration statuses
STATUS_REG_NAME = "reg:name"
STATUS_REG_REGION = "reg:region"
STATUS_REG_SCHOOL = "reg:school"
STATUS_REG_CLASS = "reg:class"

# Upload statuses
STATUS_UPLOAD_WAIT_PDF = "upload:wait_pdf"
STATUS_UPLOAD_SUBJECT = "upload:subject"
STATUS_UPLOAD_TAGS = "upload:tags"

# Search statuses
STATUS_SEARCH_SUBJECT = "search:subject"
STATUS_SEARCH_TAGS = "search:tags"
STATUS_SEARCH_RESULTS = "search:results"

# Menu status
STATUS_MENU_HOME = "menu:home"

# ---------- DATABASE SCHEMA NOTES ----------
"""
Required table structure for users table:

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL,
    name VARCHAR(255),
    region VARCHAR(100),
    school VARCHAR(255),
    class VARCHAR(50),
    status VARCHAR(50) DEFAULT 'menu:home',
    created_at DATETIME,
    
    -- Temporary upload fields
    temp_pdf_file_id VARCHAR(255),
    temp_pdf_unique_id VARCHAR(255),
    temp_pdf_name VARCHAR(255),
    temp_subject VARCHAR(100),
    temp_tags TEXT,
    
    -- Temporary search fields
    temp_search_subject VARCHAR(100),
    temp_search_tags TEXT,
    temp_search_page INT DEFAULT 1,
    
    INDEX idx_user_id (user_id),
    INDEX idx_status (status)
);

CREATE TABLE pdfs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    file_id VARCHAR(255) NOT NULL,
    file_unique_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    subject VARCHAR(100) NOT NULL,
    uploader_id BIGINT NOT NULL,
    created_at DATETIME,
    downloads INT DEFAULT 0,
    INDEX idx_subject (subject),
    INDEX idx_uploader (uploader_id)
);

CREATE TABLE pdf_tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pdf_id INT NOT NULL,
    tag VARCHAR(50) NOT NULL,
    FOREIGN KEY (pdf_id) REFERENCES pdfs(id) ON DELETE CASCADE,
    INDEX idx_tag (tag),
    INDEX idx_pdf_id (pdf_id)
);
"""
# ================== DATABASE CONNECTION ==================
def get_connection():
    """Get database connection with error handling"""
    try:
        conn = mysql.connect(
            host="Zabots1.mysql.pythonanywhere-services.com",
            user="Zabots1",
            password="users_db_pass",
            database="Zabots1$Ardayda",
            charset='utf8mb4'
        )
        return conn
    except Exception as e:
        print(f"❌ Unexpected connection error: {e}")
        return None
        
# ---------- USERS ----------

def get_user(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def add_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (user_id, status, created_at) VALUES (%s, %s, %s)",
        (user_id, STATUS_MENU_HOME, datetime.utcnow())
    )
    conn.commit()
    cursor.close()
    conn.close()

def get_user_status(user_id):
    user = get_user(user_id)
    return user['status'] if user else None

def set_status(user_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET status=%s WHERE user_id=%s", (status, user_id))
    conn.commit()
    cursor.close()
    conn.close()

def set_user_name(user_id, name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET name=%s WHERE user_id=%s",
        (name, user_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

def set_user_region(user_id, region):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET region=%s WHERE user_id=%s",
        (region, user_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

def set_user_school(user_id, school):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET school=%s WHERE user_id=%s",
        (school, user_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

def set_user_class(user_id, user_class):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET class=%s WHERE user_id=%s",
        (user_class, user_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

# ---------- TEMPORARY UPLOAD DATA ----------
def save_upload_temp(user_id, pdf_file_id, pdf_unique_id, pdf_name):
    """Save temporary upload data to user record"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE users SET 
           temp_pdf_file_id=%s, 
           temp_pdf_unique_id=%s, 
           temp_pdf_name=%s 
           WHERE user_id=%s""",
        (pdf_file_id, pdf_unique_id, pdf_name, user_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

def save_upload_subject(user_id, subject):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET temp_subject=%s WHERE user_id=%s",
        (subject, user_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

def save_upload_tags(user_id, tags_string):
    """Save tags as comma-separated string"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET temp_tags=%s WHERE user_id=%s",
        (tags_string, user_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

def get_upload_temp(user_id):
    """Get temporary upload data"""
    user = get_user(user_id)
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
    """Clear temporary upload data"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE users SET 
           temp_pdf_file_id=NULL, 
           temp_pdf_unique_id=NULL, 
           temp_pdf_name=NULL,
           temp_subject=NULL,
           temp_tags=NULL
           WHERE user_id=%s""",
        (user_id,)
    )
    conn.commit()
    cursor.close()
    conn.close()

# ---------- TEMPORARY SEARCH DATA ----------
def save_search_temp(user_id, subject, tags_string, page=1):
    """Save temporary search data"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE users SET 
           temp_search_subject=%s, 
           temp_search_tags=%s,
           temp_search_page=%s
           WHERE user_id=%s""",
        (subject, tags_string, page, user_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

def get_search_temp(user_id):
    """Get temporary search data"""
    user = get_user(user_id)
    if not user:
        return None
    
    tags = []
    if user.get("temp_search_tags"):
        tags = [t for t in user["temp_search_tags"].split(",") if t]
    
    return {
        "subject": user.get("temp_search_subject"),
        "tags": tags,
        "page": user.get("temp_search_page", 1)
    }

def clear_search_temp(user_id):
    """Clear temporary search data"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE users SET 
           temp_search_subject=NULL, 
           temp_search_tags=NULL,
           temp_search_page=NULL
           WHERE user_id=%s""",
        (user_id,)
    )
    conn.commit()
    cursor.close()
    conn.close()

# ---------- PDFs ----------
def insert_pdf(file_id, name, subject, uploader_id, file_unique_id=None):
    """
    Insert a new PDF record
    Now accepts file_unique_id parameter
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            raise Exception("Failed to connect to database")
        
        # If file_unique_id is None, generate one from file_id
        if not file_unique_id:
            file_unique_id = file_id  # Fallback, but better to use actual unique_id
            
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO pdfs 
               (file_id, file_unique_id, name, subject, uploader_id, created_at) 
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (file_id, file_unique_id, name, subject, uploader_id, datetime.utcnow())
        )
        pdf_id = cursor.lastrowid
        conn.commit()
        return pdf_id
    except mysql.connector.IntegrityError as e:
        # Handle duplicate entry specifically
        if "Duplicate entry" in str(e):
            print(f"Duplicate PDF detected: {file_unique_id}")
            # Find and return existing PDF ID
            existing = get_pdf_by_unique_id(file_unique_id)
            if existing:
                return existing['id']
        raise e
    except Exception as e:
        print(f"Error inserting PDF: {e}")
        if conn:
            conn.rollback()
        raise e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_pdf_by_unique_id(file_unique_id):
    """Get PDF by its unique ID"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM pdfs WHERE file_unique_id = %s", (file_unique_id,))
        return cursor.fetchone()
    except Exception as e:
        print(f"Error getting PDF by unique ID: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
def pdf_exists(file_unique_id):
    """
    Check if PDF with given unique_id exists
    Returns True if exists, False otherwise
    """
    if not file_unique_id:  # Add this check!
        return False
        
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM pdfs WHERE file_unique_id = %s", (file_unique_id,))
        result = cursor.fetchone()
        return result is not None
    except Exception as e:
        print(f"Error checking PDF existence: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_pdf_by_id(pdf_id):
    """Get PDF by ID"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM pdfs WHERE id=%s", (pdf_id,))
    pdf = cursor.fetchone()
    cursor.close()
    conn.close()
    return pdf

def get_user_pdfs_count(user_id):
    """Get count of PDFs uploaded by user"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM pdfs WHERE uploader_id=%s", (user_id,))
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return count

# ---------- PDF TAGS ----------

def add_pdf_tag(pdf_id, tag):
    """Add a tag to a PDF"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO pdf_tags (pdf_id, tag) VALUES (%s, %s)", (pdf_id, tag))
    conn.commit()
    cursor.close()
    conn.close()

def get_pdf_tags(pdf_id):
    """Get all tags for a PDF"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT tag FROM pdf_tags WHERE pdf_id=%s", (pdf_id,))
    tags = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return tags

# ---------- SEARCH PDFs ----------

def search_pdfs(subject, tags=None):
    """
    Search PDFs by subject and optional tags
    subject: str (mandatory)
    tags: list[str] (optional)
    Returns list of PDFs matching subject and any selected tags
    """
    if tags is None:
        tags = []
        
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if tags:
        # Join pdf_tags to filter
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
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

# ---------- ADMIN FUNCTIONS ----------

def get_user_admin_status(user_id):
    """Check if user is admin"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT is_admin FROM users WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        return result['is_admin'] if result else False
    except Exception as e:
        print(f"Error checking admin status: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def set_user_admin(user_id, admin_status=True):
    """Set or remove admin status"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET is_admin = %s WHERE user_id = %s",
            (admin_status, user_id)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error setting admin status: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_user_suspended(user_id):
    """Check if user is suspended"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT suspended FROM users WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        return result['suspended'] if result else False
    except Exception as e:
        print(f"Error checking suspended status: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def set_user_suspended(user_id, suspended_status=True):
    """Suspend or unsuspend user"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET suspended = %s WHERE user_id = %s",
            (suspended_status, user_id)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error setting suspended status: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def log_admin_action(admin_id, action, target_type, target_id, details=""):
    """Log admin action"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO ardayda_admin_logs 
               (admin_id, action, target_type, target_id, details, created_at) 
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (admin_id, action, target_type, target_id, details, datetime.utcnow())
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error logging admin action: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_admin_logs(limit=50):
    """Get recent admin logs"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT * FROM ardayda_admin_logs 
               ORDER BY created_at DESC 
               LIMIT %s""",
            (limit,)
        )
        return cursor.fetchall()
    except Exception as e:
        print(f"Error getting admin logs: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_all_admins():
    """Get list of all admins"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT user_id, name FROM users WHERE is_admin = TRUE ORDER BY name"
        )
        return cursor.fetchall()
    except Exception as e:
        print(f"Error getting admins: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_system_stats():
    """Get overall system statistics"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        stats = {}
        
        # Total users
        cursor.execute("SELECT COUNT(*) as count FROM users")
        stats['total_users'] = cursor.fetchone()['count']
        
        # Total admins
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE is_admin = TRUE")
        stats['total_admins'] = cursor.fetchone()['count']
        
        # Total suspended
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE suspended = TRUE")
        stats['total_suspended'] = cursor.fetchone()['count']
        
        # Total PDFs
        cursor.execute("SELECT COUNT(*) as count FROM pdfs")
        stats['total_pdfs'] = cursor.fetchone()['count']
        
        # Total downloads
        cursor.execute("SELECT SUM(downloads) as total FROM pdfs")
        stats['total_downloads'] = cursor.fetchone()['total'] or 0
        
        # Users joined today
        today = datetime.utcnow().date()
        cursor.execute(
            "SELECT COUNT(*) as count FROM users WHERE DATE(created_at) = %s",
            (today,)
        )
        stats['users_today'] = cursor.fetchone()['count']
        
        # PDFs uploaded today
        cursor.execute(
            "SELECT COUNT(*) as count FROM pdfs WHERE DATE(created_at) = %s",
            (today,)
        )
        stats['pdfs_today'] = cursor.fetchone()['count']
        
        return stats
    except Exception as e:
        print(f"Error getting system stats: {e}")
        return {}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()