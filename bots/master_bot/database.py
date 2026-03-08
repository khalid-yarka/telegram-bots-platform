# bots/master_bot/database.py
import logging
from master_db.connection import get_db_connection

logger = logging.getLogger(__name__)

# ==================== TABLE CREATION ====================

def create_master_tables():
    """Create master bot specific tables"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            # Create master bot commands table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS master_commands (
                id INT PRIMARY KEY AUTO_INCREMENT,
                command VARCHAR(50) NOT NULL UNIQUE,
                description TEXT,
                enabled BOOLEAN DEFAULT TRUE,
                admin_only BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Create master bot settings table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS master_settings (
                id INT PRIMARY KEY AUTO_INCREMENT,
                setting_key VARCHAR(100) NOT NULL UNIQUE,
                setting_value TEXT,
                category VARCHAR(50) DEFAULT 'general',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """)

            # Create master bot notifications table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS master_notifications (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id BIGINT NOT NULL,
                message TEXT NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_read BOOLEAN DEFAULT FALSE,
                notification_type VARCHAR(50) DEFAULT 'info'
            )
            """)

            # NEW: Create bot profiles table for descriptions and photos
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_profiles (
                bot_token VARCHAR(255) PRIMARY KEY,
                description TEXT,
                photo_file_id VARCHAR(255),
                welcome_message TEXT,
                commands TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """)

            conn.commit()
            logger.info("Master bot tables created successfully")

        except Exception as e:
            logger.error(f"Error creating master tables: {str(e)}")
            conn.rollback()
        finally:
            cursor.close()


# ==================== COMMAND OPERATIONS ====================

def add_master_command(command, description, admin_only=False):
    """Add command to master bot"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            query = """
            INSERT INTO master_commands (command, description, admin_only)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                description = VALUES(description),
                admin_only = VALUES(admin_only)
            """
            cursor.execute(query, (command, description, admin_only))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding command: {str(e)}")
            conn.rollback()
            return False
        finally:
            cursor.close()


def get_master_commands(include_disabled=False):
    """Get all master bot commands"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            if include_disabled:
                query = "SELECT * FROM master_commands ORDER BY command"
            else:
                query = "SELECT * FROM master_commands WHERE enabled = TRUE ORDER BY command"
            cursor.execute(query)
            return cursor.fetchall()
        finally:
            cursor.close()


def enable_master_command(command, enabled=True):
    """Enable or disable a master command"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            query = "UPDATE master_commands SET enabled = %s WHERE command = %s"
            cursor.execute(query, (enabled, command))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error enabling command: {str(e)}")
            conn.rollback()
            return False
        finally:
            cursor.close()


def delete_master_command(command):
    """Delete a master command"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            query = "DELETE FROM master_commands WHERE command = %s"
            cursor.execute(query, (command,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting command: {str(e)}")
            conn.rollback()
            return False
        finally:
            cursor.close()


# ==================== SETTINGS OPERATIONS ====================

def set_master_setting(key, value, category='general'):
    """Set master bot setting"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            query = """
            INSERT INTO master_settings (setting_key, setting_value, category)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                setting_value = VALUES(setting_value),
                category = VALUES(category)
            """
            cursor.execute(query, (key, value, category))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error setting master setting: {str(e)}")
            conn.rollback()
            return False
        finally:
            cursor.close()


def get_master_setting(key, default=None):
    """Get master bot setting"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT setting_value FROM master_settings WHERE setting_key = %s"
            cursor.execute(query, (key,))
            result = cursor.fetchone()
            return result['setting_value'] if result else default
        finally:
            cursor.close()


def get_all_master_settings(category=None):
    """Get all master settings, optionally filtered by category"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            if category:
                query = "SELECT * FROM master_settings WHERE category = %s ORDER BY setting_key"
                cursor.execute(query, (category,))
            else:
                query = "SELECT * FROM master_settings ORDER BY category, setting_key"
                cursor.execute(query)
            return cursor.fetchall()
        finally:
            cursor.close()


def delete_master_setting(key):
    """Delete a master setting"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            query = "DELETE FROM master_settings WHERE setting_key = %s"
            cursor.execute(query, (key,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            cursor.close()


# ==================== NOTIFICATION OPERATIONS ====================

def add_notification(user_id, message, notification_type='info'):
    """Add notification for user"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            query = """
            INSERT INTO master_notifications (user_id, message, notification_type)
            VALUES (%s, %s, %s)
            """
            cursor.execute(query, (user_id, message, notification_type))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error adding notification: {str(e)}")
            conn.rollback()
            return None
        finally:
            cursor.close()


def get_unread_notifications(user_id, limit=10):
    """Get unread notifications for user"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            query = """
            SELECT * FROM master_notifications
            WHERE user_id = %s AND is_read = FALSE
            ORDER BY sent_at DESC
            LIMIT %s
            """
            cursor.execute(query, (user_id, limit))
            return cursor.fetchall()
        finally:
            cursor.close()


def get_all_notifications(user_id, limit=50, offset=0):
    """Get all notifications for user with pagination"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            query = """
            SELECT * FROM master_notifications
            WHERE user_id = %s
            ORDER BY sent_at DESC
            LIMIT %s OFFSET %s
            """
            cursor.execute(query, (user_id, limit, offset))
            return cursor.fetchall()
        finally:
            cursor.close()


def mark_notification_read(notification_id):
    """Mark a notification as read"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            query = "UPDATE master_notifications SET is_read = TRUE WHERE id = %s"
            cursor.execute(query, (notification_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            cursor.close()


def mark_all_notifications_read(user_id):
    """Mark all user notifications as read"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            query = "UPDATE master_notifications SET is_read = TRUE WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            conn.commit()
            return cursor.rowcount
        finally:
            cursor.close()


def delete_notification(notification_id):
    """Delete a notification"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            query = "DELETE FROM master_notifications WHERE id = %s"
            cursor.execute(query, (notification_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            cursor.close()


def get_notification_count(user_id, unread_only=False):
    """Get count of notifications for user"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            if unread_only:
                query = "SELECT COUNT(*) FROM master_notifications WHERE user_id = %s AND is_read = FALSE"
            else:
                query = "SELECT COUNT(*) FROM master_notifications WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            return cursor.fetchone()[0]
        finally:
            cursor.close()


# ==================== BOT PROFILE OPERATIONS (NEW) ====================

def get_bot_profile(bot_token):
    """Get bot profile information"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT * FROM bot_profiles WHERE bot_token = %s",
                (bot_token,)
            )
            return cursor.fetchone()
        finally:
            cursor.close()


def create_or_update_bot_profile(bot_token, **kwargs):
    """Create or update bot profile"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            # Check if profile exists
            cursor.execute("SELECT bot_token FROM bot_profiles WHERE bot_token = %s", (bot_token,))
            exists = cursor.fetchone()

            if exists:
                # Update existing profile
                fields = []
                values = []
                for key, value in kwargs.items():
                    if value is not None:  # Only update provided fields
                        fields.append(f"{key} = %s")
                        values.append(value)

                if not fields:
                    return True  # Nothing to update

                values.append(bot_token)
                query = f"UPDATE bot_profiles SET {', '.join(fields)} WHERE bot_token = %s"
                cursor.execute(query, values)
            else:
                # Insert new profile
                columns = ['bot_token'] + list(kwargs.keys())
                placeholders = ['%s'] + ['%s'] * len(kwargs)
                values = [bot_token] + list(kwargs.values())

                query = f"""
                INSERT INTO bot_profiles ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                """
                cursor.execute(query, values)

            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating bot profile: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()


def update_bot_description(bot_token, description):
    """Update bot description only"""
    return create_or_update_bot_profile(bot_token, description=description)


def update_bot_photo(bot_token, photo_file_id):
    """Update bot photo only"""
    return create_or_update_bot_profile(bot_token, photo_file_id=photo_file_id)


def update_bot_welcome_message(bot_token, welcome_message):
    """Update bot welcome message only"""
    return create_or_update_bot_profile(bot_token, welcome_message=welcome_message)


def update_bot_commands(bot_token, commands):
    """Update bot commands list"""
    return create_or_update_bot_profile(bot_token, commands=commands)


def delete_bot_profile(bot_token):
    """Delete bot profile"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM bot_profiles WHERE bot_token = %s", (bot_token,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            cursor.close()


# ==================== ANALYTICS OPERATIONS (NEW) ====================

def get_command_usage_stats(limit=10):
    """Get most used commands statistics"""
    from master_db.operations import get_recent_logs

    logs = get_recent_logs(limit=1000)
    command_count = {}

    for log in logs:
        action = log.get('action_type', '')
        if action.startswith('/') or action in ['add_bot', 'delete_bot', 'view_bot']:
            command_count[action] = command_count.get(action, 0) + 1

    # Sort by count
    sorted_commands = sorted(command_count.items(), key=lambda x: x[1], reverse=True)
    return sorted_commands[:limit]


def get_user_activity_stats(days=7):
    """Get user activity statistics for last N days"""
    from master_db.operations import get_recent_logs
    from datetime import datetime, timedelta

    cutoff = datetime.now() - timedelta(days=days)
    logs = get_recent_logs(limit=5000)

    active_users = set()
    daily_activity = {}

    for log in logs:
        if log.get('timestamp') and log.get('user_id'):
            timestamp = log['timestamp']
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except:
                    continue

            if timestamp >= cutoff:
                user_id = log['user_id']
                active_users.add(user_id)

                # Count by day
                day = timestamp.strftime('%Y-%m-%d')
                daily_activity[day] = daily_activity.get(day, 0) + 1

    return {
        'total_active_users': len(active_users),
        'daily_activity': daily_activity,
        'period_days': days
    }


# ==================== INITIALIZATION ====================

# Initialize tables when module is imported
try:
    create_master_tables()
    logger.info("Master bot tables initialized")
except Exception as e:
    logger.error(f"Failed to initialize master tables: {e}")

# Add default commands (only if table is empty)
try:
    # Check if commands exist
    existing = get_master_commands(include_disabled=True)
    if not existing:
        default_commands = [
            ('/start', 'Start the master bot', False),
            ('/help', 'Show help message', False),
            ('/menu', 'Show main menu', False),
            ('/addbot', 'Add a new bot', True),
            ('/mybots', 'List your bots', False),
            ('/botinfo', 'Get bot information', False),
            ('/removebot', 'Delete a bot', True),
            ('/webhook', 'Manage webhooks', True),
            ('/logs', 'View system logs', True),
            ('/users', 'Manage bot users', True),
            ('/settings', 'Bot settings', True),
            ('/stats', 'View statistics', False),
            ('/admin', 'Super admin panel', True)
        ]

        for cmd, desc, admin in default_commands:
            add_master_command(cmd, desc, admin)

        logger.info("Default master commands added")
    else:
        logger.info("Master commands already exist, skipping defaults")
except Exception as e:
    logger.error(f"Failed to add default commands: {e}")

# Add default settings
try:
    # Check if settings exist
    existing_settings = get_all_master_settings()
    if not existing_settings:
        default_settings = [
            ('welcome_message', 'Welcome to Master Bot Controller! 👑', 'messages'),
            ('max_bots_per_user', '10', 'limits'),
            ('webhook_check_interval', '300', 'webhook'),
            ('log_retention_days', '30', 'logging'),
            ('enable_bot_registration', 'true', 'registration'),
            ('default_bot_type', 'ardayda', 'bots'),
            ('allow_public_registration', 'false', 'registration'),
            ('notification_enabled', 'true', 'notifications')
        ]

        for key, value, category in default_settings:
            set_master_setting(key, value, category)

        logger.info("Default master settings added")
    else:
        logger.info("Master settings already exist, skipping defaults")
except Exception as e:
    logger.error(f"Failed to add default settings: {e}")