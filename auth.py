import sqlite3
import bcrypt
from database import get_connection

def verify_user(username, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT emp_id, username, password_hash FROM employees WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()

    if row:
        emp_id, user, password_hash = row
        if bcrypt.checkpw(password.encode(), password_hash):
            return emp_id
    return None

def get_user_role(emp_id):
    return "admin" if emp_id == "ADMIN001" else "employee"

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())