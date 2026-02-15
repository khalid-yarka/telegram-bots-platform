import mysql.connector as mysql
from mysql.connector import Error

def get_connection():
    try:
        return mysql.connect(
            host="Zabots1.mysql.pythonanywhere-services.com",
            user="Zabots1",
            password="users_db_pass",
            database="Zabots1$Ardayda",
            charset="utf8mb4"
        )
    except Error as e:
        print(f"DB connection failed: {e}")
        return None
"""
_connection = None

def get_connection():
    global _connection
    if _connection and _connection.is_connected():
        return _connection
    try:
        _connection = mysql.connect(
            host="Zabots1.mysql.pythonanywhere-services.com",
            user="Zabots1",
            password="users_db_pass",
            database="Zabots1$Ardayda",
        )
        return _connection
    except Exception as e:
        print("DB connection error:", e)
        return None
"""   

# ----- User operations -----
def add_user(user_id):
    con = get_connection()
    if not con: return False
    try:
        cur = con.cursor()
        cur.execute("INSERT IGNORE INTO users (id,status) VALUES (%s,%s)", (user_id,"reg:name"))
        con.commit()
        return True
    except Exception as e:
        print("Add user error:", e)
        return False
    finally:
        cur.close()
        con.close()

def get_user(user_id):
    con = get_connection()
    if not con: return None
    try:
        cur = con.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE id=%s",(user_id,))
        return cur.fetchone()
    except Exception as e:
        print("Get user error:", e)
        return None
    finally:
        cur.close()
        con.close()

def get_user_status(user_id):
    user = get_user(user_id)
    return user["status"] if user else None

def set_status(user_id, status):
    con = get_connection()
    if not con: return False
    try:
        cur = con.cursor()
        cur.execute("UPDATE users SET status=%s WHERE id=%s",(status,user_id))
        con.commit()
        return True
    except Exception as e:
        print("Set status error:", e)
        return False
    finally:
        cur.close()
        con.close()

def update_user(user_id, **fields):
    if not fields: return False
    allowed = {"name","region","school","class_","status"}
    if any(k not in allowed for k in fields): return False
    con = get_connection()
    if not con: return False
    try:
        cur = con.cursor()
        keys = ", ".join(f"{k}=%s" for k in fields)
        values = list(fields.values()) + [user_id]
        cur.execute(f"UPDATE users SET {keys} WHERE id=%s",values)
        con.commit()
        return True
    except Exception as e:
        print("Update user error:", e)
        return False
    finally:
        cur.close()
        con.close()

# ----- PDF operations -----

def get_all_tags():
    con = get_connection()
    if not con: return []
    try:
        cur = con.cursor(dictionary=True)
        cur.execute("SELECT id, name FROM tags")
        return cur.fetchall()
    except Exception as e:
        print("Get tags error:", e)
        return []
    finally:
        cur.close()
        con.close()


def add_pdf(name, file_id, uploaded_by):
    con = get_connection()
    if not con: return None
    try:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO pdfs (name, file_id, uploaded_by) VALUES (%s,%s,%s)",
            (name, file_id, uploaded_by)
        )
        con.commit()
        return cur.lastrowid
    except Exception as e:
        print("Add PDF error:", e)
        return None
    finally:
        cur.close()
        con.close()


def assign_tags_to_pdf(pdf_id, tags):
    if not tags:
        return
    con = get_connection()
    if not con:
        return
    try:
        cur = con.cursor()
        for tag in tags:
            cur.execute("SELECT id FROM tags WHERE name=%s", (tag,))
            row = cur.fetchone()
            if row:
                tag_id = row[0]
            else:
                cur.execute("INSERT INTO tags (name) VALUES (%s)", (tag,))
                tag_id = cur.lastrowid

            cur.execute(
                "INSERT IGNORE INTO pdf_tags (pdf_id, tag_id) VALUES (%s,%s)",
                (pdf_id, tag_id)
            )
        con.commit()
    except Exception as e:
        print("Assign tags error:", e)
    finally:
        cur.close()
        con.close()

def get_pdf_by_id(pdf_id):
    con = get_connection()
    if not con:
        return None
    try:
        cur = con.cursor(dictionary=True)
        cur.execute("SELECT * FROM pdfs WHERE id=%s", (pdf_id,))
        return cur.fetchone()
    except Exception as e:
        print("Get PDF error:", e)
        return None
    finally:
        cur.close()
        con.close()
        

def get_pdfs_by_tags(tags):
    if not tags:
        return []
    con = get_connection()
    if not con:
        return []
    try:
        cur = con.cursor(dictionary=True)
        placeholders = ",".join(["%s"] * len(tags))
        cur.execute(
            f"""
            SELECT DISTINCT p.*
            FROM pdfs p
            JOIN pdf_tags pt ON p.id = pt.pdf_id
            JOIN tags t ON pt.tag_id = t.id
            WHERE t.name IN ({placeholders})
            """,
            tags
        )
        return cur.fetchall()
    except Exception as e:
        print("Get PDFs error:", e)
        return []
    finally:
        cur.close()
        con.close()


def increment_download(pdf_id):
    con = get_connection()
    if not con: return
    try:
        cur = con.cursor()
        cur.execute(
            "UPDATE pdfs SET downloads = downloads + 1 WHERE id=%s",
            (pdf_id,)
        )
        con.commit()
    except Exception as e:
        print("Increment download error:", e)
    finally:
        cur.close()
        con.close()


def like_pdf(pdf_id, user_id):
    con = get_connection()
    if not con:
        return False

    try:
        cur = con.cursor()

        # insert only if not already liked
        cur.execute(
            "INSERT IGNORE INTO pdf_likes (pdf_id, user_id) VALUES (%s, %s)",
            (pdf_id, user_id)
        )

        if cur.rowcount == 0:
            return False  # already liked

        cur.execute(
            "UPDATE pdfs SET likes = likes + 1 WHERE id=%s",
            (pdf_id,)
        )

        con.commit()
        return True

    except Exception as e:
        print("Like PDF error:", e)
        return False
    finally:
        cur.close()
        
        
if __name__ == '__main__':
    print(get_user(2094426161))