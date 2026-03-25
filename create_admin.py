import sqlite3
import bcrypt

DB_NAME = "attendance.db"


def create_admin():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    print("\n=== CREATE NEW ADMIN ACCOUNT ===")
    emp_id = input("Enter Admin Employee ID (e.g., ADMIN002): ")
    name = input("Enter Admin Full Name: ")
    username = input("Enter Admin Username: ")
    password = input("Enter Admin Password: ")

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    try:
        c.execute("""
            INSERT INTO employees(emp_id, name, salary_per_hour, address, contact,
                                  username, password_hash, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (emp_id, name, 0, "N/A", "0000000000", username, hashed, 1))

        conn.commit()
        print("✅ Admin created successfully.\n")

    except sqlite3.IntegrityError:
        print("❌ ERROR: Admin ID or Username already exists!\n")

    conn.close()


def update_admin_username():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    print("\n=== UPDATE ADMIN USERNAME ===")
    admin_id = input("Enter Admin Employee ID to Update: ")
    new_username = input("Enter New Username: ")

    c.execute("SELECT emp_id FROM employees WHERE emp_id=?", (admin_id,))
    if not c.fetchone():
        print("❌ Admin not found!")
    else:
        try:
            c.execute("UPDATE employees SET username=? WHERE emp_id=?", (new_username, admin_id))
            conn.commit()
            print("✅ Admin username updated successfully!\n")
        except sqlite3.IntegrityError:
            print("❌ ERROR: Username already taken!")

    conn.close()


def update_admin_password():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    print("\n=== UPDATE ADMIN PASSWORD ===")
    admin_id = input("Enter Admin Employee ID to Update: ")
    new_password = input("Enter New Password: ")

    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())

    c.execute("SELECT emp_id FROM employees WHERE emp_id=?", (admin_id,))
    if not c.fetchone():
        print("❌ Admin not found!")
    else:
        c.execute("UPDATE employees SET password_hash=? WHERE emp_id=?", (hashed, admin_id))
        conn.commit()
        print("✅ Admin password updated successfully!\n")

    conn.close()


def menu():
    while True:
        print("\n========== ADMIN MANAGEMENT MENU ==========")
        print("1. Create New Admin")
        print("2. Update Admin Username")
        print("3. Update Admin Password")
        print("4. Exit")
        print("===========================================")

        choice = input("Enter your choice: ")

        if choice == "1":
            create_admin()
        elif choice == "2":
            update_admin_username()
        elif choice == "3":
            update_admin_password()
        elif choice == "4":
            print("✅ Exiting Admin Manager Tool.")
            break
        else:
            print("❌ Invalid choice! Try again.\n")


if __name__ == "__main__":
    menu()