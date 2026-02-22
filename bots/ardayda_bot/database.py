import mysql.connector as mysql
from mysql.connector import Error

# ================= CONNECTION =================
_connection = None


def get_connection():
    global _connection
    try:
        if _connection and _connection.is_connected():
            return _connection

        _connection = mysql.connect(
            host="Zabots1.mysql.pythonanywhere-services.com",
            user="Zabots1",
            password="users_db_pass",
            database="Zabots1$Ardayda",
            charset="utf8mb4",
            autocommit=True
        )
        return _connection

    except Error as e:
        print("DB connection error:", e)
        _connection = None
        return None


# ================= USERS =================
def add_user(user_id):
    con = get_connection()
    if not con:
        return False

    cur = con.cursor()
    try:
        cur.execute(
            "INSERT IGNORE INTO users (id, status) VALUES (%s, %s)",
            (user_id, "reg:name")
        )
        return True
    except Exception as e:
        print("Add user error:", e)
        return False
    finally:
        cur.close()


def get_user(user_id):
    con = get_connection()
    if not con:
        return None

    cur = con.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
        return cur.fetchone()
    except Exception as e:
        print("Get user error:", e)
        return None
    finally:
        cur.close()


def get_user_status(user_id):
    user = get_user(user_id)
    return user["status"] if user else None


def set_status(user_id, status):
    con = get_connection()
    if not con:
        return False

    cur = con.cursor()
    try:
        cur.execute(
            "UPDATE users SET status=%s WHERE id=%s",
            (status, user_id)
        )
        return True
    except Exception as e:
        print("Set status error:", e)
        return False
    finally:
        cur.close()


def update_user(user_id, **fields):
    if not fields:
        return False

    allowed = {"name", "region", "school", "class_", "status"}
    for key in fields:
        if key not in allowed:
            return False

    con = get_connection()
    if not con:
        return False

    cur = con.cursor()
    try:
        query = ", ".join(f"{k}=%s" for k in fields)
        values = list(fields.values()) + [user_id]
        cur.execute(f"UPDATE users SET {query} WHERE id=%s", values)
        return True
    except Exception as e:
        print("Update user error:", e)
        return False
    finally:
        cur.close()


# ================= TAGS =================
def get_tags_by_category(category):
    con = get_connection()
    if not con:
        return []

    cur = con.cursor(dictionary=True)
    try:
        cur.execute(
            "SELECT id, name FROM tags WHERE category=%s ORDER BY name",
            (category,)
        )
        return cur.fetchall()
    except Exception as e:
        print("Get tags error:", e)
        return []
    finally:
        cur.close()


def get_or_create_tag(name, category):
    con = get_connection()
    if not con:
        return None

    cur = con.cursor()
    try:
        cur.execute(
            "SELECT id FROM tags WHERE name=%s AND category=%s",
            (name, category)
        )
        row = cur.fetchone()
        if row:
            return row[0]

        cur.execute(
            "INSERT INTO tags (name, category) VALUES (%s, %s)",
            (name, category)
        )
        return cur.lastrowid

    except Exception as e:
        print("Create tag error:", e)
        return None
    finally:
        cur.close()


# ================= PDF =================
def add_pdf(name, file_id, uploaded_by):
    con = get_connection()
    if not con:
        return None

    cur = con.cursor()
    try:
        cur.execute(
            """
            INSERT INTO pdfs (name, file_id, uploaded_by)
            VALUES (%s, %s, %s)
            """,
            (name, file_id, uploaded_by)
        )
        return cur.lastrowid
    except Exception as e:
        print("Add PDF error:", e)
        return None
    finally:
        cur.close()


def get_pdf_by_id(pdf_id):
    con = get_connection()
    if not con:
        return None

    cur = con.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM pdfs WHERE id=%s", (pdf_id,))
        return cur.fetchone()
    except Exception as e:
        print("Get PDF error:", e)
        return None
    finally:
        cur.close()


def assign_tag_to_pdf(pdf_id, tag_name, category):
    tag_id = get_or_create_tag(tag_name, category)
    if not tag_id:
        return False

    con = get_connection()
    if not con:
        return False

    cur = con.cursor()
    try:
        cur.execute(
            "INSERT IGNORE INTO pdf_tags (pdf_id, tag_id) VALUES (%s, %s)",
            (pdf_id, tag_id)
        )
        return True
    except Exception as e:
        print("Assign tag error:", e)
        return False
    finally:
        cur.close()


def get_pdfs_by_tags(tag_ids):
    if not tag_ids:
        return []

    con = get_connection()
    if not con:
        return []

    cur = con.cursor(dictionary=True)
    try:
        placeholders = ",".join(["%s"] * len(tag_ids))
        cur.execute(
            f"""
            SELECT DISTINCT p.*
            FROM pdfs p
            JOIN pdf_tags pt ON p.id = pt.pdf_id
            WHERE pt.tag_id IN ({placeholders})
            """,
            tag_ids
        )
        return cur.fetchall()
    except Exception as e:
        print("Search PDFs error:", e)
        return []
    finally:
        cur.close()


# ================= METRICS =================
def increment_download(pdf_id):
    con = get_connection()
    if not con:
        return False

    cur = con.cursor()
    try:
        cur.execute(
            "UPDATE pdfs SET downloads = downloads + 1 WHERE id=%s",
            (pdf_id,)
        )
        return True
    except Exception as e:
        print("Download increment error:", e)
        return False
    finally:
        cur.close()


def like_pdf(pdf_id, user_id):
    con = get_connection()
    if not con:
        return False

    cur = con.cursor()
    try:
        cur.execute(
            "INSERT IGNORE INTO pdf_likes (pdf_id, user_id) VALUES (%s, %s)",
            (pdf_id, user_id)
        )

        if cur.rowcount == 0:
            return False

        cur.execute(
            "UPDATE pdfs SET likes = likes + 1 WHERE id=%s",
            (pdf_id,)
        )
        return True

    except Exception as e:
        print("Like PDF error:", e)
        return False
    finally:
        cur.close()