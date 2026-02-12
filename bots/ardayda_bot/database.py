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


def add_user(user_id):
    con = get_connection()
    if not con:
        return False
    cur = con.cursor()
    cur.execute(
        "INSERT IGNORE INTO users (id, status) VALUES (%s, %s)",
        (user_id, "reg:name")
    )
    con.commit()
    cur.close()
    con.close()
    return True


def get_user(user_id):
    con = get_connection()
    if not con:
        return None
    cur = con.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    row = cur.fetchone()
    cur.close()
    con.close()
    return row


def get_user_status(user_id):
    con = get_connection()
    if not con:
        return None
    cur = con.cursor(dictionary=True)
    cur.execute("SELECT status FROM users WHERE id=%s", (user_id,))
    row = cur.fetchone()
    cur.close()
    con.close()
    return row["status"] if row else None


def set_status(user_id, status):
    con = get_connection()
    if not con:
        return False
    cur = con.cursor()
    cur.execute("UPDATE users SET status=%s WHERE id=%s", (status, user_id))
    con.commit()
    cur.close()
    con.close()
    return True


def update_user(user_id, **fields):
    if not fields:
        return False

    allowed = {"name", "region", "school", "class_", "status"}
    if any(f not in allowed for f in fields):
        return False

    con = get_connection()
    if not con:
        return False

    cur = con.cursor()
    keys = ", ".join(f"{k}=%s" for k in fields)
    values = list(fields.values()) + [user_id]
    cur.execute(f"UPDATE users SET {keys} WHERE id=%s", values)
    con.commit()
    cur.close()
    con.close()
    return True