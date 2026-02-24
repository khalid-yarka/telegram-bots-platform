# bots/ardayda_bot/database.py

import mysql.connector
from master_db.connection import get_connection
from datetime import datetime

# ---------- USERS ----------

def get_user(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def add_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (user_id, status, created_at) VALUES (%s, %s, %s)",
                   (user_id, 'menu:home', datetime.utcnow()))
    conn.commit()
    cursor.close()
    conn.close()

def get_user_status(user_id):
    user = get_user(user_id)
    return user['status'] if user else None

def set_status(user_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET status=%s WHERE user_id=%s", (status, user_id))
    conn.commit()
    cursor.close()
    conn.close()


# ---------- PDFs ----------

def insert_pdf(file_id, name, subject, uploader_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO pdfs (file_id, name, subject, uploader_id, created_at) VALUES (%s, %s, %s, %s, %s)",
        (file_id, name, subject, uploader_id, datetime.utcnow())
    )
    pdf_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()
    return pdf_id

def check_pdf_exists(file_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM pdfs WHERE file_id=%s", (file_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result is not None

def get_pdf_by_id(pdf_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM pdfs WHERE id=%s", (pdf_id,))
    pdf = cursor.fetchone()
    cursor.close()
    conn.close()
    return pdf

# ---------- PDF TAGS ----------

def add_pdf_tag(pdf_id, tag):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO pdf_tags (pdf_id, tag) VALUES (%s, %s)", (pdf_id, tag))
    conn.commit()
    cursor.close()
    conn.close()

def get_pdf_tags(pdf_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT tag FROM pdf_tags WHERE pdf_id=%s", (pdf_id,))
    tags = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return tags

# ---------- SEARCH PDFs ----------

def search_pdfs(subject, tags=[]):
    """
    subject: str (mandatory)
    tags: list[str] (optional)
    Returns list of PDFs matching subject and any selected tags
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if tags:
        # Join pdf_tags to filter
        format_strings = ','.join(['%s'] * len(tags))
        query = f"""
        SELECT DISTINCT p.*
        FROM pdfs p
        LEFT JOIN pdf_tags t ON p.id = t.pdf_id
        WHERE p.subject = %s
        AND t.tag IN ({format_strings})
        ORDER BY p.created_at DESC
        """
        params = [subject] + tags
    else:
        query = """
        SELECT *
        FROM pdfs
        WHERE subject = %s
        ORDER BY created_at DESC
        """
        params = [subject]

    cursor.execute(query, params)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results