import logging
from master_db.connection import get_db_connection

logger = logging.getLogger(__name__)

def create_ardayda_tables():
    """Create Ardayda bot specific tables"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            # Create ardayda users table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS ardayda_users (
                id INT PRIMARY KEY AUTO_INCREMENT,
                telegram_id BIGINT UNIQUE NOT NULL,
                full_name VARCHAR(255),
                university VARCHAR(255),
                faculty VARCHAR(255),
                year_of_study INT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Create ardayda courses table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS ardayda_courses (
                id INT PRIMARY KEY AUTO_INCREMENT,
                course_name VARCHAR(255) NOT NULL,
                course_code VARCHAR(50) UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Create ardayda materials table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS ardayda_materials (
                id INT PRIMARY KEY AUTO_INCREMENT,
                course_id INT,
                material_name VARCHAR(255) NOT NULL,
                material_type ENUM('note', 'book', 'video', 'exam'),
                file_url VARCHAR(500),
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            conn.commit()
            logger.info("Ardayda bot tables created successfully")

        except Exception as e:
            logger.error(f"Error creating ardayda tables: {str(e)}")
            conn.rollback()
        finally:
            cursor.close()

def add_ardayda_user(telegram_id, full_name, university=None, faculty=None):
    """Add user to ardayda database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            query = """
            INSERT INTO ardayda_users (telegram_id, full_name, university, faculty)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                full_name = VALUES(full_name),
                university = VALUES(university),
                faculty = VALUES(faculty)
            """
            cursor.execute(query, (telegram_id, full_name, university, faculty))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding ardayda user: {str(e)}")
            conn.rollback()
            return False
        finally:
            cursor.close()

def get_ardayda_user(telegram_id):
    """Get ardayda user info"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT * FROM ardayda_users WHERE telegram_id = %s"
            cursor.execute(query, (telegram_id,))
            return cursor.fetchone()
        finally:
            cursor.close()

def add_ardayda_course(course_name, course_code, description=None):
    """Add course to ardayda database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            query = """
            INSERT INTO ardayda_courses (course_name, course_code, description)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                course_name = VALUES(course_name),
                description = VALUES(description)
            """
            cursor.execute(query, (course_name, course_code, description))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding course: {str(e)}")
            conn.rollback()
            return False
        finally:
            cursor.close()

def get_ardayda_courses():
    """Get all ardayda courses"""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            query = "SELECT * FROM ardayda_courses ORDER BY course_name"
            cursor.execute(query)
            return cursor.fetchall()
        finally:
            cursor.close()

# Initialize tables when module is imported
try:
    create_ardayda_tables()
    logger.info("Ardayda bot tables initialized")

    # Add some default courses
    default_courses = [
        ("Computer Science", "CS101", "Introduction to Computer Science"),
        ("Mathematics", "MATH101", "Calculus and Algebra"),
        ("Physics", "PHY101", "Basic Physics Principles"),
        ("Chemistry", "CHEM101", "General Chemistry"),
        ("Biology", "BIO101", "Introduction to Biology")
    ]

    for course_name, course_code, description in default_courses:
        add_ardayda_course(course_name, course_code, description)

    logger.info("Default ardayda courses added")

except Exception as e:
    logger.error(f"Failed to initialize ardayda tables: {e}")