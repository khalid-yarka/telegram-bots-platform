#master_db/operations
import logging
from datetime import datetime
from master_db.connection import get_db_connection
from config import config

logger = logging.getLogger(__name__)

# ==================== BOT OPERATIONS ====================

def bot_exists(bot_token):
    """Check if bot exists in database"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT bot_token FROM system_bots WHERE bot_token = %s"
            cursor.execute(query, (bot_token,))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

def get_bot_by_token(bot_token):
    """Get bot information by token"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT * FROM system_bots WHERE bot_token = %s"
            cursor.execute(query, (bot_token,))
            return cursor.fetchone()
        finally:
            cursor.close()

def add_bot(bot_token, bot_name, bot_type, owner_id, bot_username=None):
    """Add new bot to system"""
    if bot_exists(bot_token):
        logger.warning(f"Bot {bot_token[:10]}... already exists")
        return False

    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            query = """
            INSERT INTO system_bots
            (bot_token, bot_name, bot_username, bot_type, owner_id, created_at, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                bot_token, bot_name, bot_username, bot_type,
                owner_id, datetime.now(), True
            ))
            conn.commit()
            logger.info(f"Bot {bot_name} added by owner {owner_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding bot: {str(e)}")
            conn.rollback()
            return False
        finally:
            cursor.close()

def get_all_bots():
    """Get all bots from database"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT * FROM system_bots WHERE is_active = TRUE ORDER BY created_at DESC"
            cursor.execute(query)
            return cursor.fetchall()
        finally:
            cursor.close()

def update_bot_activity(bot_token):
    """Update bot's last seen timestamp"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            query = "UPDATE system_bots SET last_seen = %s WHERE bot_token = %s"
            cursor.execute(query, (datetime.now(), bot_token))
            conn.commit()
        finally:
            cursor.close()

def delete_bot(bot_token, requester_id):
    """Delete bot from system"""
    # Check if requester is bot owner or super admin
    bot = get_bot_by_token(bot_token)
    if not bot:
        return False

    # Allow deletion if: owner or super admin
    if bot['owner_id'] != requester_id and requester_id not in config.SUPER_ADMINS:
        return False

    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            query = "DELETE FROM system_bots WHERE bot_token = %s"
            cursor.execute(query, (bot_token,))
            conn.commit()
            logger.info(f"Bot {bot_token[:10]}... deleted by {requester_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting bot: {str(e)}")
            conn.rollback()
            return False
        finally:
            cursor.close()

# ==================== PERMISSION OPERATIONS ====================

def check_permission(bot_token, user_id):
    """Check user permission for a bot"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            query = """
            SELECT permission FROM bot_permissions
            WHERE bot_token = %s AND user_id = %s
            """
            cursor.execute(query, (bot_token, user_id))
            result = cursor.fetchone()
            return result['permission'] if result else None
        finally:
            cursor.close()

def can_manage_bot(bot_token, user_id):
    """Check if user can manage bot (owner or admin)"""
    # SUPER ADMINS CAN DO ANYTHING
    if user_id in config.SUPER_ADMINS:
        return True

    permission = check_permission(bot_token, user_id)
    return permission in ['owner', 'admin']

def add_permission(bot_token, user_id, permission='user', notes=None):
    """Add or update user permission"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            query = """
            INSERT INTO bot_permissions (bot_token, user_id, permission, granted_at, notes)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE permission = VALUES(permission), notes = VALUES(notes)
            """
            cursor.execute(query, (
                bot_token, user_id, permission, datetime.now(), notes
            ))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding permission: {str(e)}")
            conn.rollback()
            return False
        finally:
            cursor.close()

# ==================== LOG OPERATIONS ====================

def add_log_entry(bot_token, action_type, user_id=None, details=None):
    """Add entry to system logs"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            query = """
            INSERT INTO system_logs (timestamp, bot_token, user_id, action_type, details)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                datetime.now(), bot_token, user_id, action_type, details
            ))
            conn.commit()

            # Update bot activity
            update_bot_activity(bot_token)

        except Exception as e:
            logger.error(f"Error adding log: {str(e)}")
        finally:
            cursor.close()

def get_recent_logs(bot_token=None, limit=50):
    """Get recent system logs"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            if bot_token:
                query = """
                SELECT * FROM system_logs
                WHERE bot_token = %s
                ORDER BY timestamp DESC
                LIMIT %s
                """
                cursor.execute(query, (bot_token, limit))
            else:
                query = """
                SELECT * FROM system_logs
                ORDER BY timestamp DESC
                LIMIT %s
                """
                cursor.execute(query, (limit,))
            return cursor.fetchall()
        finally:
            cursor.close()

# ==================== WEBHOOK OPERATIONS ====================

def update_webhook_status(bot_token, status, error=None):
    """Update webhook status"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            if status == 'active':
                query = """
                UPDATE webhook_monitor
                SET status = %s, last_success = %s, last_checked = %s,
                    last_error = NULL, total_failures = 0
                WHERE bot_token = %s
                """
                cursor.execute(query, (status, datetime.now(), datetime.now(), bot_token))
            else:
                query = """
                UPDATE webhook_monitor
                SET status = %s, last_checked = %s, last_error = %s,
                    total_failures = total_failures + 1
                WHERE bot_token = %s
                """
                cursor.execute(query, (status, datetime.now(), error, bot_token))
            conn.commit()
        except Exception as e:
            logger.error(f"Error updating webhook status: {str(e)}")
            conn.rollback()
        finally:
            cursor.close()

def get_webhook_status(bot_token):
    """Get webhook status for a bot"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT * FROM webhook_monitor WHERE bot_token = %s"
            cursor.execute(query, (bot_token,))
            return cursor.fetchone()
        finally:
            cursor.close()

# ==================== SETTINGS OPERATIONS ====================

def get_setting(bot_token, key, default=None):
    """Get bot setting"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            query = """
            SELECT setting_value FROM bot_settings
            WHERE bot_token = %s AND setting_key = %s
            """
            cursor.execute(query, (bot_token, key))
            result = cursor.fetchone()
            return result['setting_value'] if result else default
        finally:
            cursor.close()

def set_setting(bot_token, key, value):
    """Set bot setting"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            query = """
            INSERT INTO bot_settings (bot_token, setting_key, setting_value)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)
            """
            cursor.execute(query, (bot_token, key, value))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error setting value: {str(e)}")
            conn.rollback()
            return False
        finally:
            cursor.close()

# ==================== SUPER ADMIN OPERATIONS ====================

def is_super_admin(user_id):
    """Check if user is super admin"""
    return user_id in config.SUPER_ADMINS

def get_user_bots(user_id):
    """Get all bots a user has access to"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            query1 = """
            SELECT b.*, bp.permission
            FROM system_bots b
            JOIN bot_permissions bp ON b.bot_token = bp.bot_token
            WHERE bp.user_id = %s AND b.is_active = TRUE
            ORDER BY b.created_at DESC
            """
            
            query = "SELECT bot_token FROM system_bots WHERE user_id=%s"
            cursor.execute(query, (user_id,))
            return cursor.fetchall()
        finally:
            cursor.close()

def get_bot_users(bot_token):
    """Get all users with access to a bot"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            query = """
            SELECT bp.* FROM bot_permissions bp
            WHERE bp.bot_token = %s
            ORDER BY bp.permission DESC, bp.granted_at DESC
            """
            cursor.execute(query, (bot_token,))
            return cursor.fetchall()
        finally:
            cursor.close()