# bots/ardayda_bot/database.py
import mysql.connector as mysql
from mysql.connector import Error

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
    except Error as e:
        print(f"❌ Database connection failed: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected connection error: {e}")
        return None

# ================== USER OPERATIONS ==================
def get_user(user_id):
    """Get user by ID"""
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

def update_user(user_id, **fields):
    """Update multiple user fields at once"""
    if not fields:
        return False, "No fields to update"

    con = get_connection()
    if not con:
        return False, "Database connection failed"

    cursor = None
    try:
        allowed_fields = {'name', 'school', 'class'}
        for field in fields:
            if field not in allowed_fields:
                return False, f"Invalid field: {field}"

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

def add_user(user_id):
    """Add a new user if not exists"""
    con = get_connection()
    if not con:
        return False
    cursor = None
    try:
        cursor = con.cursor()
        query = "INSERT IGNORE INTO users (id) VALUES (%s)"
        cursor.execute(query, (user_id,))
        con.commit()
        return True
    except Error as e:
        print(f"❌ Error adding user: {e}")
        if con:
            con.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()

# ================== READ OPERATIONS ==================
def get_all_users(limit=15):
    con = get_connection()
    if not con:
        return []
    cursor = None
    try:
        cursor = con.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users LIMIT %s", (limit,))
        return cursor.fetchall()
    except Error as e:
        print(f"❌ Error getting all users: {e}")
        return []
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

def get_users_by_school(school_name):
    """Get users from specific school"""
    con = get_connection()
    if not con:
        return []
    cursor = None
    try:
        cursor = con.cursor(dictionary=True)
        query = "SELECT * FROM users WHERE school = %s ORDER BY name"
        cursor.execute(query, (school_name,))
        return cursor.fetchall()
    except Error as e:
        print(f"❌ Error getting users by school: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if con:
            con.close()

# ================== DELETE OPERATIONS ==================
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
        return cursor.rowcount
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

# ================== STATISTICS ==================
def get_user_count():
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

# ================== TEST CONNECTION ==================
def test_connection():
    con = get_connection()
    if not con:
        print("❌ Connection test failed")
        return False
    try:
        cursor = con.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        print("✅ Database connection test passed")
        return True
    except Error as e:
        print(f"❌ Connection test failed: {e}")
        return False
    finally:
        cursor.close()
        con.close()

# ================== RUN TEST ==================
if __name__ == "__main__":
    print("🔧 Testing database module...")
    if test_connection():
        print("✅ Database module is ready!")
    else:
        print("❌ Database module has issues")