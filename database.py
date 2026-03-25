import sqlite3
from datetime import datetime
import os

DB_NAME = "attendance.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Employees Table
    c.execute('''CREATE TABLE IF NOT EXISTS employees(
                    emp_id TEXT PRIMARY KEY,
                    name TEXT,
                    salary_per_hour REAL,
                    address TEXT,
                    contact TEXT,
                    username TEXT UNIQUE,
                    password_hash TEXT,
                    is_active INTEGER)''')

    # Attendance Table
    c.execute('''CREATE TABLE IF NOT EXISTS attendance(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    emp_id TEXT,
                    date TEXT,
                    punch_in TEXT,
                    punch_out TEXT,
                    work_hours REAL,
                    photo_path TEXT,
                    FOREIGN KEY(emp_id) REFERENCES employees(emp_id))''')

    # Salary Table
    c.execute('''CREATE TABLE IF NOT EXISTS salary(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    emp_id TEXT,
                    month TEXT,
                    total_hours REAL,
                    salary_paid REAL,
                    FOREIGN KEY(emp_id) REFERENCES employees(emp_id))''')

    conn.commit()
    conn.close()


def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)