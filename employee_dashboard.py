def show(emp_id):
    import streamlit as st
    from datetime import datetime
    import pandas as pd
    from database import get_connection

    st.title("👨‍💼 Employee Dashboard")

    conn = get_connection()
    c = conn.cursor()

    # -----------------------------------------------------------
    # ✅ CAMERA CAPTURE FUNCTION
    # -----------------------------------------------------------

    # -----------------------------------------------------------
    # ✅ PUNCH IN (Store FULL datetime)
    # -----------------------------------------------------------
    if st.button("✅ Punch In"):

        now = datetime.now()

        # Check if already punched in today
        c.execute("""
            SELECT id, punch_in 
            FROM attendance 
            WHERE emp_id=? AND date=?
        """, (emp_id, now.date().isoformat()))

        existing = c.fetchone()

        if existing and existing[1] is not None:
            st.warning("⚠️ Already punched in today!")
        else:
            photo_path = capture_photo(emp_id)

            c.execute("""
                INSERT INTO attendance (emp_id, date, punch_in, work_hours)
                VALUES (?, ?, ?, ?, ?)
            """, (emp_id, now.date().isoformat(), now.isoformat(), 0)

            conn.commit()
            st.success("✅ Punch In Recorded Successfully")

    # -----------------------------------------------------------
    # ✅ PUNCH OUT (Correct Time Calculation)
    # -----------------------------------------------------------
    if st.button("⛔ Punch Out"):

        now = datetime.now()

        c.execute("""
            SELECT id, punch_in, punch_out 
            FROM attendance 
            WHERE emp_id=? AND date=?
        """, (emp_id, now.date().isoformat()))

        row = c.fetchone()

        if not row:
            st.error("❌ No punch-in found for today!")
        else:
            att_id, punch_in, punch_out = row

            if punch_out is not None:
                st.warning("⚠️ Already punched out today!")
            else:
                punch_in_dt = datetime.fromisoformat(punch_in)

                diff_hours = (now - punch_in_dt).total_seconds() / 3600

                c.execute("""
                    UPDATE attendance
                    SET punch_out=?, work_hours=?
                    WHERE id=?
                """, (now.isoformat(), diff_hours, att_id))

                conn.commit()
                st.success(f"✅ Punch Out Recorded — Worked {diff_hours:.2f} hours")

    # -----------------------------------------------------------
    # ✅ ATTENDANCE SUMMARY TABLE
    # -----------------------------------------------------------
    st.subheader("📅 Attendance Summary")

    df = pd.read_sql("""
        SELECT * FROM attendance WHERE emp_id=?
    """, conn, params=(emp_id,))

    st.dataframe(df, use_container_width=True)

    # -----------------------------------------------------------
    # ✅ WEEKLY & MONTHLY WORK HOURS
    # -----------------------------------------------------------
    if not df.empty:

        df["date"] = pd.to_datetime(df["date"], errors='coerce')
        df["work_hours"] = pd.to_numeric(df["work_hours"], errors='coerce').fillna(0)

        # Weekly Calculation
        current_week = df[df["date"].dt.isocalendar().week == datetime.now().isocalendar().week]
        week_hours = current_week["work_hours"].sum()

        # Monthly Calculation
        current_month = df[df["date"].dt.month == datetime.now().month]
        month_hours = current_month["work_hours"].sum()

        st.metric("🗓 This Week Hours", f"{week_hours:.2f} hrs")
        st.metric("📆 This Month Hours", f"{month_hours:.2f} hrs")

    else:
        st.info("No attendance data found.")
