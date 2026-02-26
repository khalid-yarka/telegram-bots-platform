import logging
from master_db.connection import get_db_connection

logger = logging.getLogger(__name__)

def create_dhalinyaro_tables():
    """Create Dhalinyaro bot specific tables"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            # Create dhalinyaro users table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS dhalinyaro_users (
                id INT PRIMARY KEY AUTO_INCREMENT,
                telegram_id BIGINT UNIQUE NOT NULL,
                nickname VARCHAR(100),
                age INT,
                location VARCHAR(255),
                interests TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Create dhalinyaro events table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS dhalinyaro_events (
                id INT PRIMARY KEY AUTO_INCREMENT,
                event_name VARCHAR(255) NOT NULL,
                event_type ENUM('meetup', 'workshop', 'sports', 'cultural', 'other'),
                description TEXT,
                event_date DATETIME,
                location VARCHAR(255),
                organizer_id BIGINT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Create dhalinyaro groups table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS dhalinyaro_groups (
                id INT PRIMARY KEY AUTO_INCREMENT,
                group_name VARCHAR(255) NOT NULL,
                group_type VARCHAR(100),
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            conn.commit()
            logger.info("Dhalinyaro bot tables created successfully")

        except Exception as e:
            logger.error(f"Error creating dhalinyaro tables: {str(e)}")
            conn.rollback()
        finally:
            cursor.close()

def add_dhalinyaro_user(telegram_id, nickname=None, age=None, location=None):
    """Add user to dhalinyaro database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            query = """
            INSERT INTO dhalinyaro_users (telegram_id, nickname, age, location)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                nickname = VALUES(nickname),
                age = VALUES(age),
                location = VALUES(location)
            """
            cursor.execute(query, (telegram_id, nickname, age, location))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding dhalinyaro user: {str(e)}")
            conn.rollback()
            return False
        finally:
            cursor.close()

def get_dhalinyaro_user(telegram_id):
    """Get dhalinyaro user info"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT * FROM dhalinyaro_users WHERE telegram_id = %s"
            cursor.execute(query, (telegram_id,))
            return cursor.fetchone()
        finally:
            cursor.close()

def add_dhalinyaro_event(event_name, event_type, description, event_date, location, organizer_id):
    """Add event to dhalinyaro database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            query = """
            INSERT INTO dhalinyaro_events
            (event_name, event_type, description, event_date, location, organizer_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (event_name, event_type, description, event_date, location, organizer_id))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding event: {str(e)}")
            conn.rollback()
            return False
        finally:
            cursor.close()

def get_upcoming_events(limit=10):
    """Get upcoming dhalinyaro events"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            query = """
            SELECT * FROM dhalinyaro_events
            WHERE event_date >= NOW()
            ORDER BY event_date
            LIMIT %s
            """
            cursor.execute(query, (limit,))
            return cursor.fetchall()
        finally:
            cursor.close()

def add_dhalinyaro_group(group_name, group_type, description=None):
    """Add group to dhalinyaro database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            query = """
            INSERT INTO dhalinyaro_groups (group_name, group_type, description)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                group_type = VALUES(group_type),
                description = VALUES(description)
            """
            cursor.execute(query, (group_name, group_type, description))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding group: {str(e)}")
            conn.rollback()
            return False
        finally:
            cursor.close()

def get_dhalinyaro_groups():
    """Get all dhalinyaro groups"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT * FROM dhalinyaro_groups ORDER BY group_name"
            cursor.execute(query)
            return cursor.fetchall()
        finally:
            cursor.close()

# Initialize tables when module is imported
try:
    create_dhalinyaro_tables()
    logger.info("Dhalinyaro bot tables initialized")

    # Add some default groups
    default_groups = [
        ("Tech Enthusiasts", "technology", "For tech lovers and innovators"),
        ("Sports Club", "sports", "Football, basketball, and fitness activities"),
        ("Arts Community", "arts", "Music, painting, poetry, and culture"),
        ("Study Network", "education", "Study groups and career development"),
        ("Social Activists", "social", "Community service and social change")
    ]

    for group_name, group_type, description in default_groups:
        add_dhalinyaro_group(group_name, group_type, description)

    logger.info("Default dhalinyaro groups added")

except Exception as e:
    logger.error(f"Failed to initialize dhalinyaro tables: {e}")