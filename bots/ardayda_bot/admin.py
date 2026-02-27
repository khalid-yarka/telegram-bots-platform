# bots/ardayda_bot/admin.py

from datetime import datetime, timedelta
import logging
from typing import List, Dict, Any, Optional, Tuple

from bots.ardayda_bot import database
# Import admin_utils for any needed functions
from bots.ardayda_bot.admin_utils import is_admin

logger = logging.getLogger(__name__)

# Constants
USERS_PER_PAGE = 5
PDFS_PER_PAGE = 5
LOGS_PER_PAGE = 5


# ==================== Admin Verification ====================

# Note: is_admin function is now in admin_utils.py
# Keep this for backward compatibility if needed
def get_admin_status(user_id: int) -> bool:
    """Alias for is_admin - maintained for backward compatibility"""
    return is_admin(user_id)


def require_admin(func):
    """Decorator to require admin privileges"""
    def wrapper(bot, call, *args, **kwargs):
        user_id = call.from_user.id
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "⛔ Admin access required!")
            return
        return func(bot, call, *args, **kwargs)
    return wrapper


# ==================== Admin Actions Logging ====================
def log_admin_action(admin_id: int, action: str, target_type: str, target_id: int, details: str = ""):
    """Log an admin action"""
    try:
        with database.get_db_connection() as (conn, cursor):
            cursor.execute(
                """INSERT INTO ardayda_admin_logs 
                   (admin_id, action, target_type, target_id, details, created_at) 
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (admin_id, action, target_type, target_id, details, datetime.utcnow())
            )
            logger.info(f"Admin log: {admin_id} - {action} - {target_type}:{target_id}")
    except Exception as e:
        logger.error(f"Error logging admin action: {e}")



# ==================== User Management ====================
def get_all_users(page: int = 1, per_page: int = USERS_PER_PAGE) -> Tuple[List[Dict], int]:
    """Get paginated list of all users"""
    try:
        with database.get_db_connection() as (conn, cursor):
            # Get total count
            cursor.execute("SELECT COUNT(*) as total FROM users")
            total = cursor.fetchone()['total']
            total_pages = (total + per_page - 1) // per_page
            
            # Get paginated users
            offset = (page - 1) * per_page
            cursor.execute(
                """SELECT user_id, name, region, school, class, status, 
                          created_at, is_admin 
                   FROM users 
                   ORDER BY created_at DESC 
                   LIMIT %s OFFSET %s""",
                (per_page, offset)
            )
            users = cursor.fetchall()
            
            return users, total_pages
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return [], 1



def get_user_details(user_id: int) -> Optional[Dict]:
    """Get detailed user info including PDF count"""
    try:
        user = database.get_user(user_id)
        if user:
            user['pdf_count'] = database.get_user_pdfs_count(user_id)
        return user
    except Exception as e:
        logger.error(f"Error getting user details: {e}")
        return None


def get_user_pdfs(user_id: int, page: int = 1, per_page: int = PDFS_PER_PAGE) -> Tuple[List[Dict], int]:
    """Get paginated list of PDFs uploaded by a user"""
    conn = None
    cursor = None
    try:
        conn = database.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get total count
        cursor.execute("SELECT COUNT(*) as total FROM pdfs WHERE uploader_id = %s", (user_id,))
        total = cursor.fetchone()['total']
        total_pages = (total + per_page - 1) // per_page
        
        # Get paginated PDFs
        offset = (page - 1) * per_page
        cursor.execute(
            """SELECT id, file_id, name, subject, created_at, downloads 
               FROM pdfs 
               WHERE uploader_id = %s 
               ORDER BY created_at DESC 
               LIMIT %s OFFSET %s""",
            (user_id, per_page, offset)
        )
        pdfs = cursor.fetchall()
        
        # Get tags for each PDF
        for pdf in pdfs:
            pdf['tags'] = database.get_pdf_tags(pdf['id'])
        
        return pdfs, total_pages
    except Exception as e:
        logger.error(f"Error getting user PDFs: {e}")
        return [], 1
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def suspend_user(admin_id: int, user_id: int) -> bool:
    """Suspend a user"""
    conn = None
    cursor = None
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        
        # Add suspended column if not exists (run once)
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN suspended BOOLEAN DEFAULT FALSE")
            conn.commit()
        except:
            pass  # Column might already exist
        
        cursor.execute("UPDATE users SET suspended = TRUE WHERE user_id = %s", (user_id,))
        conn.commit()
        
        log_admin_action(admin_id, 'suspend_user', 'user', user_id)
        return True
    except Exception as e:
        logger.error(f"Error suspending user: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def unsuspend_user(admin_id: int, user_id: int) -> bool:
    """Unsuspend a user"""
    conn = None
    cursor = None
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET suspended = FALSE WHERE user_id = %s", (user_id,))
        conn.commit()
        
        log_admin_action(admin_id, 'unsuspend_user', 'user', user_id)
        return True
    except Exception as e:
        logger.error(f"Error unsuspending user: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def make_admin(admin_id: int, user_id: int) -> bool:
    """Make a user admin"""
    conn = None
    cursor = None
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_admin = TRUE WHERE user_id = %s", (user_id,))
        conn.commit()
        
        log_admin_action(admin_id, 'make_admin', 'user', user_id)
        return True
    except Exception as e:
        logger.error(f"Error making admin: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def remove_admin(admin_id: int, user_id: int) -> bool:
    """Remove admin privileges"""
    conn = None
    cursor = None
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_admin = FALSE WHERE user_id = %s", (user_id,))
        conn.commit()
        
        log_admin_action(admin_id, 'remove_admin', 'user', user_id)
        return True
    except Exception as e:
        logger.error(f"Error removing admin: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ==================== PDF Management ====================

def get_all_pdfs(page: int = 1, per_page: int = PDFS_PER_PAGE) -> Tuple[List[Dict], int]:
    """Get paginated list of all PDFs"""
    conn = None
    cursor = None
    try:
        conn = database.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get total count
        cursor.execute("SELECT COUNT(*) as total FROM pdfs")
        total = cursor.fetchone()['total']
        total_pages = (total + per_page - 1) // per_page
        
        # Get paginated PDFs
        offset = (page - 1) * per_page
        cursor.execute(
            """SELECT p.*, u.name as uploader_name 
               FROM pdfs p
               LEFT JOIN users u ON p.uploader_id = u.user_id
               ORDER BY p.created_at DESC 
               LIMIT %s OFFSET %s""",
            (per_page, offset)
        )
        pdfs = cursor.fetchall()
        
        return pdfs, total_pages
    except Exception as e:
        logger.error(f"Error getting PDFs: {e}")
        return [], 1
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_pdf_details(pdf_id: int) -> Optional[Dict]:
    """Get detailed PDF info with uploader and tags"""
    try:
        pdf = database.get_pdf_by_id(pdf_id)
        if pdf:
            pdf['tags'] = database.get_pdf_tags(pdf_id)
            uploader = database.get_user(pdf['uploader_id'])
            pdf['uploader_name'] = uploader.get('name') if uploader else 'Unknown'
        return pdf
    except Exception as e:
        logger.error(f"Error getting PDF details: {e}")
        return None


def delete_pdf(admin_id: int, pdf_id: int) -> bool:
    """Delete a PDF and its tags"""
    conn = None
    cursor = None
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        
        # Delete tags first (foreign key should handle this, but just in case)
        cursor.execute("DELETE FROM pdf_tags WHERE pdf_id = %s", (pdf_id,))
        
        # Delete PDF
        cursor.execute("DELETE FROM pdfs WHERE id = %s", (pdf_id,))
        conn.commit()
        
        log_admin_action(admin_id, 'delete_pdf', 'pdf', pdf_id)
        return True
    except Exception as e:
        logger.error(f"Error deleting PDF: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ==================== Statistics ====================
def get_user_stats() -> Dict:
    """Get user statistics"""
    conn = None
    cursor = None
    try:
        conn = database.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Total users
        cursor.execute("SELECT COUNT(*) as total FROM users")
        total_users = cursor.fetchone()['total']
        
        # Users joined today (Somalia time)
        today = database.somalia_now().date()
        cursor.execute(
            "SELECT COUNT(*) as total FROM users WHERE DATE(created_at) = %s",
            (today,)
        )
        today_users = cursor.fetchone()['total']
        
        # Users joined this week (Somalia time)
        week_ago = database.somalia_now() - timedelta(days=7)
        cursor.execute(
            "SELECT COUNT(*) as total FROM users WHERE created_at >= %s",
            (week_ago,)
        )
        week_users = cursor.fetchone()['total']
        
        # Admins count
        cursor.execute("SELECT COUNT(*) as total FROM users WHERE is_admin = TRUE")
        admin_count = cursor.fetchone()['total']
        
        return {
            'total_users': total_users,
            'today_users': today_users,
            'week_users': week_users,
            'admin_count': admin_count
        }
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return {}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_pdf_stats() -> Dict:
    """Get PDF statistics"""
    conn = None
    cursor = None
    try:
        conn = database.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Total PDFs
        cursor.execute("SELECT COUNT(*) as total FROM pdfs")
        total_pdfs = cursor.fetchone()['total']
        
        # PDFs uploaded today
        today = datetime.utcnow().date()
        cursor.execute(
            "SELECT COUNT(*) as total FROM pdfs WHERE DATE(created_at) = %s",
            (today,)
        )
        today_pdfs = cursor.fetchone()['total']
        
        # Total downloads
        cursor.execute("SELECT SUM(downloads) as total FROM pdfs")
        total_downloads = cursor.fetchone()['total'] or 0
        
        # Top subjects
        cursor.execute(
            """SELECT subject, COUNT(*) as count, SUM(downloads) as downloads 
               FROM pdfs 
               GROUP BY subject 
               ORDER BY count DESC 
               LIMIT 5"""
        )
        top_subjects = cursor.fetchall()
        
        return {
            'total_pdfs': total_pdfs,
            'today_pdfs': today_pdfs,
            'total_downloads': total_downloads,
            'top_subjects': top_subjects
        }
    except Exception as e:
        logger.error(f"Error getting PDF stats: {e}")
        return {}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ==================== Admin Logs ====================

def get_admin_logs(page: int = 1, per_page: int = LOGS_PER_PAGE) -> Tuple[List[Dict], int]:
    """Get paginated admin logs"""
    conn = None
    cursor = None
    try:
        conn = database.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get total count
        cursor.execute("SELECT COUNT(*) as total FROM ardayda_admin_logs")
        total = cursor.fetchone()['total']
        total_pages = (total + per_page - 1) // per_page
        
        # Get paginated logs
        offset = (page - 1) * per_page
        cursor.execute(
            """SELECT * FROM ardayda_admin_logs 
               ORDER BY created_at DESC 
               LIMIT %s OFFSET %s""",
            (per_page, offset)
        )
        logs = cursor.fetchall()
        
        return logs, total_pages
    except Exception as e:
        logger.error(f"Error getting admin logs: {e}")
        return [], 1
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def clear_admin_logs(admin_id: int) -> bool:
    """Clear all admin logs (super admin only)"""
    conn = None
    cursor = None
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ardayda_admin_logs")
        conn.commit()
        
        log_admin_action(admin_id, 'clear_logs', 'system', 0)
        return True
    except Exception as e:
        logger.error(f"Error clearing logs: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()