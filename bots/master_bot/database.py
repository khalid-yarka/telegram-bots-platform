#bots/master_bot/database
import logging
from master_db.connection import get_db_connection

logger = logging.getLogger(__name__)

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

            conn.commit()
            logger.info("Master bot tables created successfully")

        except Exception as e:
            logger.error(f"Error creating master tables: {str(e)}")
            conn.rollback()
        finally:
            cursor.close()

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

# Initialize tables when module is imported
try:
    create_master_tables()
    logger.info("Master bot tables initialized")
except Exception as e:
    logger.error(f"Failed to initialize master tables: {e}")

# Add default commands (only if table is empty)
try:
    default_commands = [
        ('/start', 'Start the master bot', False),
        ('/help', 'Show help message', False),
        ('/addbot', 'Add a new bot', True),
        ('/mybots', 'List your bots', False),
        ('/botinfo', 'Get bot information', False),
        ('/removebot', 'Delete a bot', True),
        ('/webhook', 'Manage webhooks', True),
        ('/logs', 'View system logs', True),
        ('/users', 'Manage bot users', True),
        ('/settings', 'Bot settings', True),
        ('/admin', 'Super admin panel', True)
    ]

    for cmd, desc, admin in default_commands:
        add_master_command(cmd, desc, admin)

    logger.info("Default master commands added")
except Exception as e:
    logger.error(f"Failed to add default commands: {e}")

# Add default settings
try:
    default_settings = [
        ('welcome_message', 'Welcome to Master Bot Controller! 👑', 'messages'),
        ('max_bots_per_user', '10', 'limits'),
        ('webhook_check_interval', '300', 'webhook'),
        ('log_retention_days', '30', 'logging'),
        ('enable_bot_registration', 'true', 'registration')
    ]

    for key, value, category in default_settings:
        set_master_setting(key, value, category)

    logger.info("Default master settings added")
except Exception as e:
    logger.error(f"Failed to add default settings: {e}")