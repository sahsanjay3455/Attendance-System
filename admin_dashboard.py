def show(emp_id):
    import streamlit as st
    import pandas as pd
    from database import get_connection
    import bcrypt
    import io
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    import matplotlib.pyplot as plt

    st.title("🛠 Admin Dashboard")

    conn = get_connection()
    c = conn.cursor()

    # =============================================================
    # ✅ KPI CARDS
    # =============================================================
    st.subheader("📊 Overview")

    total_emp = c.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
    active_emp = c.execute("SELECT COUNT(*) FROM employees WHERE is_active=1").fetchone()[0]
    inactive_emp = c.execute("SELECT COUNT(*) FROM employees WHERE is_active=0").fetchone()[0]

    col1, col2, col3 = st.columns(3)
    col1.metric("👥 Total Employees", total_emp)
    col2.metric("✅ Active Employees", active_emp)
    col3.metric("⛔ Inactive Employees", inactive_emp)

    # =============================================================
    # ✅ MAIN TABS
    # =============================================================
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "➕ Add Employee",
        "📝 Update Employees",
        "📂 Attendance Report",
        "📊 Salary Report",
        "🛡 Admin Management"
    ])

    # =============================================================
    # ✅ TAB 1: ADD EMPLOYEE
    # =============================================================
    with tab1:
        st.subheader("➕ Add New Employee")

        emp_id_input = st.text_input("Employee ID", key="add_emp_id")
        name = st.text_input("Full Name", key="add_emp_name")
        salary = st.number_input("Hourly Salary", min_value=0.0, key="add_emp_salary")
        addr = st.text_area("Address", key="add_emp_addr")
        contact = st.text_input("Contact Number", key="add_emp_contact")
        uname = st.text_input("Login Username", key="add_emp_username")
        pwd = st.text_input("Password", type="password", key="add_emp_password")

        if st.button("Create Employee ✅", key="btn_create_emp"):
            if emp_id_input and name and uname and pwd:
                hash_pw = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt())
                try:
                    c.execute("""
                        INSERT INTO employees 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (emp_id_input, name, salary, addr, contact, uname, hash_pw, 1))
                    conn.commit()
                    st.success("✅ Employee Added Successfully")
                except:
                    st.error("❌ Employee ID or Username already exists")
            else:
                st.warning("⚠️ Please fill all required fields!")

    # =============================================================
    # ✅ TAB 2: UPDATE + DELETE
    # =============================================================
    with tab2:
        st.subheader("📝 Update / Delete Employee")

        df = pd.read_sql("SELECT * FROM employees", conn)
        st.dataframe(df, use_container_width=True)

        if not df.empty:
            selected = st.selectbox("Select Employee ID", df["emp_id"].tolist(), key="update_sel_emp")
            emp_data = df[df["emp_id"] == selected].iloc[0]

            st.info(f"💰 Current Salary: {emp_data['salary_per_hour']} per hour")

            new_sal = st.number_input("Update Salary", value=float(emp_data["salary_per_hour"]), key="update_salary")
            new_addr = st.text_area("Update Address", value=emp_data["address"], key="update_addr")
            new_contact = st.text_input("Update Contact", value=emp_data["contact"], key="update_contact")
            new_status = st.selectbox("Update Status", [1, 0], 
                                      index=0 if emp_data["is_active"] else 1, key="update_status")

            colA, colB = st.columns(2)

            if colA.button("✅ Update Employee", key="btn_update_emp"):
                c.execute("""
                    UPDATE employees 
                    SET salary_per_hour=?, address=?, contact=?, is_active=? 
                    WHERE emp_id=?
                """, (new_sal, new_addr, new_contact, new_status, selected))
                conn.commit()
                st.success("✅ Employee Updated Successfully")

            if colB.button("🗑 Delete Employee", key="btn_delete_emp"):
                c.execute("DELETE FROM attendance WHERE emp_id=?", (selected,))
                c.execute("DELETE FROM employees WHERE emp_id=?", (selected,))
                conn.commit()
                st.warning(f"🗑 Employee {selected} Deleted Successfully!")

    # =============================================================
    # ✅ TAB 3: ATTENDANCE REPORT
    # =============================================================
    with tab3:
        st.subheader("📂 Attendance Records")

        df_att = pd.read_sql("""
            SELECT a.*, e.salary_per_hour,
                   (a.work_hours * e.salary_per_hour) AS total_salary
            FROM attendance a
            LEFT JOIN employees e ON a.emp_id = e.emp_id
        """, conn)

        st.dataframe(df_att, use_container_width=True)

        st.download_button("⬇ Download Attendance CSV",
                           df_att.to_csv(index=False).encode(),
                           "attendance.csv", "text/csv",
                           key="download_att_csv")

        st.markdown("---")
        st.subheader("🗑 Delete Attendance Data")

        col_del1, col_del2 = st.columns(2)

        if not df_att.empty:
            record_ids = df_att["id"].tolist()
            del_id = col_del1.selectbox("Select Attendance ID to Delete", record_ids,
                                        key="delete_att_select")

            if col_del1.button("Delete Selected Record 🗑", key="btn_del_record"):
                c.execute("DELETE FROM attendance WHERE id=?", (del_id,))
                conn.commit()
                st.success(f"✅ Deleted record {del_id}")

        if col_del2.button("Delete ALL Attendance Records 🚨", key="btn_del_all_att"):
            c.execute("DELETE FROM attendance")
            conn.commit()
            st.warning("⚠️ All Attendance Records Deleted!")

    # =============================================================
    # ✅ TAB 4: SALARY REPORT
    # =============================================================
    with tab4:
        st.subheader("💰 Salary Summary Per Employee")

        df_emp = pd.read_sql("SELECT emp_id, name, salary_per_hour FROM employees", conn)
        emp_list = df_emp["emp_id"].tolist()

        selected_emp = st.selectbox("Select Employee", emp_list, key="salary_emp_select")

        col_m, col_y = st.columns(2)
        month = col_m.selectbox("Select Month", list(range(1, 13)), key="salary_month")
        year = col_y.selectbox("Select Year", list(range(2020, 2035)), key="salary_year")

        query = """
            SELECT a.date, a.work_hours, e.salary_per_hour, e.name
            FROM attendance a
            LEFT JOIN employees e ON a.emp_id = e.emp_id
            WHERE a.emp_id = ?
            AND strftime('%m', a.date) = ?
            AND strftime('%Y', a.date) = ?
        """
        df_salary = pd.read_sql(query, conn, params=(selected_emp, f"{month:02d}", str(year)))

        if df_salary.empty:
            st.info("No attendance data found for this month.")
        else:
            df_salary["daily_salary"] = df_salary["work_hours"] * df_salary["salary_per_hour"]
            total_hours = df_salary["work_hours"].sum()
            total_salary = df_salary["daily_salary"].sum()

            st.metric("Total Hours Worked", f"{total_hours:.2f} hrs")
            st.metric("Total Salary", f"₹{total_salary:.2f}")

            st.dataframe(df_salary, use_container_width=True)

            st.subheader("📊 Attendance Chart")

            fig, ax = plt.subplots(figsize=(10, 4))
            ax.bar(df_salary["date"], df_salary["work_hours"], color="#4CAF50")
            ax.set_xlabel("Date")
            ax.set_ylabel("Hours Worked")
            ax.set_title(f"Attendance Chart - {month}/{year}")
            ax.tick_params(axis='x', rotation=45)

            st.pyplot(fig)

            st.subheader("📄 Salary Slip PDF")

            if st.button("Generate Salary Slip", key="btn_generate_pdf"):
                buffer = io.BytesIO()
                pdf = canvas.Canvas(buffer, pagesize=A4)

                pdf.setFont("Helvetica-Bold", 16)
                pdf.drawString(50, 800, "Salary Slip")

                pdf.setFont("Helvetica", 12)
                pdf.drawString(50, 770, f"Employee ID: {selected_emp}")
                pdf.drawString(50, 750, f"Name: {df_salary['name'].iloc[0]}")
                pdf.drawString(50, 730, f"Month: {month}-{year}")
                pdf.drawString(50, 710, f"Total Hours: {total_hours:.2f}")
                pdf.drawString(50, 690, f"Salary per Hour: ₹{df_salary['salary_per_hour'].iloc[0]:.2f}")
                pdf.drawString(50, 670, f"Total Salary: ₹{total_salary:.2f}")

                pdf.save()

                st.download_button(
                    "⬇ Download Salary Slip PDF",
                    buffer.getvalue(),
                    f"salary_slip_{selected_emp}_{month}_{year}.pdf",
                    "application/pdf",
                    key="download_salary_pdf"
                )

    # =============================================================
    # ✅ TAB 5: ADMIN MANAGEMENT
    # =============================================================
    with tab5:
        st.subheader("🛡 Admin Management")

        action = st.selectbox(
            "Choose Action",
            ["Create New Admin", "Update Admin Username", "Update Admin Password"],
            key="admin_action"
        )

        # ✅ CREATE ADMIN
        if action == "Create New Admin":
            new_admin_id = st.text_input("Admin Employee ID", key="admin_new_id")
            new_admin_name = st.text_input("Full Name", key="admin_new_name")
            new_admin_username = st.text_input("Username", key="admin_new_username")
            new_admin_password = st.text_input("Password", type="password", key="admin_new_password")

            if st.button("✅ Create Admin", key="btn_create_admin"):
                if new_admin_id and new_admin_name and new_admin_username and new_admin_password:
                    hashed_pw = bcrypt.hashpw(new_admin_password.encode(), bcrypt.gensalt())
                    try:
                        c.execute("""
                            INSERT INTO employees(emp_id, name, salary_per_hour, address, contact,
                                username, password_hash, is_active)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (new_admin_id, new_admin_name, 0, "N/A", "0000000000",
                              new_admin_username, hashed_pw, 1))
                        conn.commit()
                        st.success("✅ Admin created successfully!")
                    except:
                        st.error("❌ Admin ID or Username already exists!")
                else:
                    st.warning("⚠ Fill all fields!")

        # ✅ UPDATE ADMIN USERNAME
        elif action == "Update Admin Username":
            admins = pd.read_sql("SELECT emp_id, username FROM employees WHERE emp_id LIKE 'ADMIN%'", conn)

            if admins.empty:
                st.warning("No admins found!")
            else:
                adm = st.selectbox("Select Admin ID", admins["emp_id"].tolist(), key="admin_update_sel")
                new_user = st.text_input("New Username", key="admin_update_username")

                if st.button("✅ Update Username", key="btn_update_admin_username"):
                    try:
                        c.execute("UPDATE employees SET username=? WHERE emp_id=?", (new_user, adm))
                        conn.commit()
                        st.success("✅ Username updated!")
                    except:
                        st.error("❌ Username already in use!")

        # ✅ UPDATE ADMIN PASSWORD
        elif action == "Update Admin Password":
            admins = pd.read_sql("SELECT emp_id FROM employees WHERE emp_id LIKE 'ADMIN%'", conn)

            if admins.empty:
                st.warning("No admins found!")
            else:
                adm = st.selectbox("Select Admin ID", admins["emp_id"].tolist(), key="admin_pw_sel")
                new_pass = st.text_input("New Password", type="password", key="admin_pw_new")

                if st.button("✅ Update Password", key="btn_update_admin_pass"):
                    hashed_pw = bcrypt.hashpw(new_pass.encode(), bcrypt.gensalt())
                    c.execute("UPDATE employees SET password_hash=? WHERE emp_id=?", (hashed_pw, adm))
                    conn.commit()
                    st.success("✅ Password updated successfully!")