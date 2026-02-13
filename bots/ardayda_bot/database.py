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

# ---------- Users ----------
def add_user(user_id):
    con = get_connection()
    if not con: return False
    cur = con.cursor()
    cur.execute("INSERT IGNORE INTO users (id, status) VALUES (%s,%s)", (user_id, "reg:name"))
    con.commit()
    cur.close()
    con.close()
    return True

def get_user(user_id):
    con = get_connection()
    if not con: return None
    cur = con.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    row = cur.fetchone()
    cur.close()
    con.close()
    return row

def get_user_status(user_id):
    con = get_connection()
    if not con: return None
    cur = con.cursor(dictionary=True)
    cur.execute("SELECT status FROM users WHERE id=%s", (user_id,))
    row = cur.fetchone()
    cur.close()
    con.close()
    return row["status"] if row else None

def set_status(user_id, status):
    con = get_connection()
    if not con: return False
    cur = con.cursor()
    cur.execute("UPDATE users SET status=%s WHERE id=%s", (status,user_id))
    con.commit()
    cur.close()
    con.close()
    return True

def update_user(user_id, **fields):
    if not fields: return False
    allowed = {"name","region","school","class_","status"}
    if any(k not in allowed for k in fields): return False
    con = get_connection()
    if not con: return False
    cur = con.cursor()
    keys = ", ".join(f"{k}=%s" for k in fields)
    values = list(fields.values()) + [user_id]
    cur.execute(f"UPDATE users SET {keys} WHERE id=%s", values)
    con.commit()
    cur.close()
    con.close()
    return True

# ---------- Tags ----------
def add_tag(name):
    con = get_connection()
    if not con: return False
    cur = con.cursor()
    cur.execute("INSERT IGNORE INTO tags (name) VALUES (%s)", (name,))
    con.commit()
    cur.close()
    con.close()
    return True

def get_all_tags():
    con = get_connection()
    if not con: return []
    cur = con.cursor(dictionary=True)
    cur.execute("SELECT * FROM tags ORDER BY name")
    tags = cur.fetchall()
    cur.close()
    con.close()
    return tags

# ---------- PDFs ----------
def add_pdf(name, file_id, uploader_id):
    con = get_connection()
    if not con: return None
    cur = con.cursor()
    cur.execute("INSERT INTO pdfs (name,file_id,uploaded_by) VALUES (%s,%s,%s)", (name,file_id,uploader_id))
    pdf_id = cur.lastrowid
    con.commit()
    cur.close()
    con.close()
    return pdf_id

def assign_tags_to_pdf(pdf_id, tag_names):
    if not tag_names: return
    con = get_connection()
    if not con: return
    cur = con.cursor()
    placeholders = ",".join(["%s"]*len(tag_names))
    cur.execute(f"SELECT id FROM tags WHERE name IN ({placeholders})", tag_names)
    tag_ids = [row[0] for row in cur.fetchall()]
    for tid in tag_ids:
        cur.execute("INSERT IGNORE INTO pdf_tags (pdf_id, tag_id) VALUES (%s,%s)", (pdf_id,tid))
    con.commit()
    cur.close()
    con.close()

def get_pdfs_by_tags(tags):
    if not tags: return []
    con = get_connection()
    if not con: return []
    cur = con.cursor(dictionary=True)
    placeholders = ",".join(["%s"]*len(tags))
    query = f"""
        SELECT DISTINCT p.id,p.name,p.file_id,p.downloads,p.likes
        FROM pdfs p
        JOIN pdf_tags pt ON pt.pdf_id = p.id
        JOIN tags t ON t.id = pt.tag_id
        WHERE t.name IN ({placeholders})
        GROUP BY p.id
    """
    cur.execute(query, tags)
    results = cur.fetchall()
    cur.close()
    con.close()
    return results

def increment_download(pdf_id):
    con = get_connection()
    if not con: return
    cur = con.cursor()
    cur.execute("UPDATE pdfs SET downloads = downloads+1 WHERE id=%s", (pdf_id,))
    con.commit()
    cur.close()
    con.close()

def like_pdf(pdf_id):
    con = get_connection()
    if not con: return
    cur = con.cursor()
    cur.execute("UPDATE pdfs SET likes = likes+1 WHERE id=%s", (pdf_id,))
    con.commit()
    cur.close()
    con.close()