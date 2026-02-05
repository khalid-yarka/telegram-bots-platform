# bots/ardayda_bot/database.py
import mysql.connector as mysql
from mysql.connector import Error
import time

# ============ DATABASE CONNECTION ============
def get_connection():
    """Get database connection with error handling"""
    try:
        conn = mysql.connect(
            host="Zabots1.mysql.pythonanywhere-services.com",
            user="Zabots1",
            password="users_db_pass",
            database="Zabots1$Ardayda",
            charset='utf8mb4',
            connection_timeout=60
        )
        return conn
    except Error as e:
        print(f"❌ Database connection failed: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected connection error: {e}")
        return None

# ============ USER CHECK FUNCTIONS ============
def user_exists(user_id):
    """Check if user exists in database"""
    con = get_connection()
    if not con:
        return False
    
    cursor = None
    try:
        cursor = con.cursor()
        cursor.execute("SELECT * FROM users WHERE id = %s LIMIT 1", (user_id,))
        return cursor.fetchone() is not None
    except Error as e:
        print(f"❌ Error checking user existence: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error checking user: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()

def get_user_status(user_id):
    """Get which fields are already filled for user"""
    con = get_connection()
    if not con:
        return {'exists': False}
    
    cursor = None
    try:
        cursor = con.cursor(dictionary=True)
        cursor.execute("SELECT name, school, class FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return {'exists': False}
        
        # Determine next step
        if user['name'] is None:
            next_step = 'name'
        else:
            next_step = 'complete'
        
        return {
            'exists': True,
            'name': user['name'],
            'next_step': next_step,
            'complete': next_step == 'complete'
        }
    except Error as e:
        print(f"❌ Error getting user status: {e}")
        return {'exists': False, 'error': str(e)}
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()

# ============ CREATE USER (STEP BY STEP) ============
def create_user_record(user_id):
    """Create empty user record with only ID"""
    con = get_connection()
    if not con:
        return False
    
    cursor = None
    try:
        # Check if already exists
        if user_exists(user_id):
            return True  # Already exists, nothing to do
        
        cursor = con.cursor()
        query = "INSERT INTO users (id,) VALUES (%s,)"
        cursor.execute(query, (user_id,))
        con.commit()
        return True
    except Error as e:
        print(f"❌ Error creating user record: {e}")
        if con:
            con.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()

# ============ SET INDIVIDUAL FIELDS ============
def set_user_name(user_id, name):
    """Set user name only"""
    
    con = get_connection()
    if not con:
        return False, "Database connection failed"
    
    cursor = None
    try:
        cursor = con.cursor()
        query = "UPDATE users SET name = %s WHERE id = %s"
        cursor.execute(query, (name.strip(), user_id))
        con.commit()
        return True, "successfully uldated name [✓]"
        
    except Error as e:
        print(f"❌ Error setting name: {e}")
        if con:
            con.rollback()
        return False, f"Database error: {e}"
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()
"""
def set_user_school(user_id, school):
    """Set user school only"""
    if not school:
        return False, "School cannot be empty"
    
    # Validate school is a number
    try:
        school_int = int(school)
        if school_int <= 0:
            return False, "School must be a positive number"
    except ValueError:
        return False, "School must be a number"
    
    con = get_connection()
    if not con:
        return False, "Database connection failed"
    
    cursor = None
    try:
        cursor = con.cursor()
        query = "UPDATE users SET school = %s WHERE id = %s"
        cursor.execute(query, (school_int, user_id))
        con.commit()
        
        if cursor.rowcount == 0:
            return False, "User not found"
        return True, "School saved successfully"
    except Error as e:
        print(f"❌ Error setting school: {e}")
        if con:
            con.rollback()
        return False, f"Database error: {e}"
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()

def set_user_class(user_id, class_):
    """Set user class only"""
    if not class_:
        return False, "Class cannot be empty"
    
    # Validate class is a number and in reasonable range
    try:
        class_int = int(class_)
        if not (1 <= class_int <= 12):  # Assuming classes 1-12
            return False, "Class must be between 1 and 12"
    except ValueError:
        return False, "Class must be a number"
    
    con = get_connection()
    if not con:
        return False, "Database connection failed"
    
    cursor = None
    try:
        cursor = con.cursor()
        query = "UPDATE users SET class = %s WHERE id = %s"
        cursor.execute(query, (class_int, user_id))
        con.commit()
        
        if cursor.rowcount == 0:
            return False, "User not found"
        return True, "Class saved successfully"
    except Error as e:
        print(f"❌ Error setting class: {e}")
        if con:
            con.rollback()
        return False, f"Database error: {e}"
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()
"""
# ============ READ OPERATIONS ============
def get_all_users(limit=15):
    """Get all users"""
    con = get_connection()
    if not con:
        return []
    
    cursor = None
    try:
        cursor = con.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users LIMIT %s",(limit,))
        return cursor.fetchall()
    except Error as e:
        print(f"❌ Error getting all users: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()

def get_user_by_id(user_id):
    """Get single user by ID"""
    con = get_connection()
    if not con:
        return None
    
    cursor = None
    try:
        cursor = con.cursor(dictionary=True)
        query = "SELECT * FROM users WHERE id = %s"
        cursor.execute(query, (user_id,))
        return cursor.fetchone()
    except Error as e:
        print(f"❌ Error getting user: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()

def get_complete_user(user_id):
    """Get user only if all fields are filled"""
    con = get_connection()
    if not con:
        return None
    
    cursor = None
    try:
        cursor = con.cursor(dictionary=True)
        query = """
            SELECT * FROM users 
            WHERE id = %s 
            AND name IS NOT NULL 
            AND school IS NOT NULL 
            AND class IS NOT NULL
        """
        cursor.execute(query, (user_id,))
        return cursor.fetchone()
    except Error as e:
        print(f"❌ Error getting complete user: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()

def get_users_by_school(school_id):
    """Get users from specific school"""
    con = get_connection()
    if not con:
        return []
    
    cursor = None
    try:
        cursor = con.cursor(dictionary=True)
        query = "SELECT * FROM users WHERE school = %s ORDER BY name"
        cursor.execute(query, (school_id,))
        return cursor.fetchall()
    except Error as e:
        print(f"❌ Error getting users by school: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()

# ============ UPDATE MULTIPLE FIELDS ============
def update_user(user_id, **fields):
    """Update multiple user fields at once"""
    if not fields:
        return False, "No fields to update"
    
    con = get_connection()
    if not con:
        return False, "Database connection failed"
    
    cursor = None
    try:
        # Validate fields
        allowed_fields = {'name', 'school', 'class'}
        for field in fields:
            if field not in allowed_fields:
                return False, f"Invalid field: {field}"
        
        # Build dynamic query
        set_clause = ", ".join([f"{key} = %s" for key in fields.keys()])
        values = list(fields.values())
        values.append(user_id)
        
        cursor = con.cursor()
        query = f"UPDATE users SET {set_clause} WHERE id = %s"
        cursor.execute(query, values)
        con.commit()
        
        if cursor.rowcount == 0:
            return False, "User not found"
        return True, f"Updated {len(fields)} field(s) successfully"
    except Error as e:
        print(f"❌ Error updating user: {e}")
        if con:
            con.rollback()
        return False, f"Database error: {e}"
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()

# ============ DELETE OPERATIONS ============
def delete_user(user_id):
    """Delete user by ID"""
    con = get_connection()
    if not con:
        return False
    
    cursor = None
    try:
        cursor = con.cursor()
        query = "DELETE FROM users WHERE id = %s"
        cursor.execute(query, (user_id,))
        con.commit()
        return cursor.rowcount > 0
    except Error as e:
        print(f"❌ Error deleting user: {e}")
        if con:
            con.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()

def delete_incomplete_users():
    """Delete users with missing required fields"""
    con = get_connection()
    if not con:
        return 0
    
    cursor = None
    try:
        cursor = con.cursor()
        query = """
            DELETE FROM users 
            WHERE name IS NULL 
            OR school IS NULL 
            OR class IS NULL
        """
        cursor.execute(query)
        con.commit()
        deleted_count = cursor.rowcount
        print(f"🗑️ Deleted {deleted_count} incomplete users")
        return deleted_count
    except Error as e:
        print(f"❌ Error deleting incomplete users: {e}")
        if con:
            con.rollback()
        return 0
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()

# ============ STATISTICS ============
def get_user_count():
    """Get total number of users"""
    con = get_connection()
    if not con:
        return 0
    
    cursor = None
    try:
        cursor = con.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        return cursor.fetchone()[0]
    except Error as e:
        print(f"❌ Error getting user count: {e}")
        return 0
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()

def get_complete_user_count():
    """Get number of users with all fields filled"""
    con = get_connection()
    if not con:
        return 0
    
    cursor = None
    try:
        cursor = con.cursor()
        query = """
            SELECT COUNT(*) FROM users 
            WHERE name IS NOT NULL 
            AND school IS NOT NULL 
            AND class IS NOT NULL
        """
        cursor.execute(query)
        return cursor.fetchone()[0]
    except Error as e:
        print(f"❌ Error getting complete user count: {e}")
        return 0
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()



# ============ TEST FUNCTIONS ============
def test_connection():
    """Test database connection"""
    con = get_connection()
    if not con:
        print("❌ Connection test failed")
        return False
    
    try:
        cursor = con.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print("✅ Database connection test passed")
        return True
    except Error as e:
        print(f"❌ Connection test failed: {e}")
        return False
    finally:
        cursor.close()
        con.close()

# Test the module when run directly
if __name__ == "__main__":
    print("🔧 Testing database module...")
    if test_connection():
        print("✅ Database module is ready!")
    else:
        print("❌ Database module has issues")