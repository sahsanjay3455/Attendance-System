def show(emp_id):
    import streamlit as st
    from datetime import datetime
    import pandas as pd
    from database import get_connection
    import tempfile
    import os

    st.title("👨‍💼 Employee Dashboard")

    conn = get_connection()
    c = conn.cursor()

    # -----------------------------------------------------------
    # ✅ PHOTO DIRECTORY (Always Writable)
    # -----------------------------------------------------------
    photos_dir = os.path.join(tempfile.gettempdir(), "photos")
    os.makedirs(photos_dir, exist_ok=True)

    # -----------------------------------------------------------
    # ✅ ALWAYS SHOW CAMERA
    # -----------------------------------------------------------
    st.subheader("📸 Capture Your Photo (Required for Punch In)")
    photo = st.camera_input("Take a photo")

    if photo:
        st.session_state["captured_photo"] = photo
        st.success("✅ Photo captured successfully!")
    else:
        st.session_state["captured_photo"] = None

    # -----------------------------------------------------------
    # ✅ PUNCH IN
    # -----------------------------------------------------------
    st.subheader("✅ Punch In / Punch Out")

    if st.button("✅ Punch In"):

        # Check if photo exists
        if not st.session_state.get("captured_photo"):
            st.error("❌ Please capture a photo before punching in.")
            return

        now = datetime.now()

        # Check existing punch-in
        c.execute("""
            SELECT id, punch_in 
            FROM attendance 
            WHERE emp_id=? AND date=?
        """, (emp_id, now.date().isoformat()))

        existing = c.fetchone()

        if existing and existing[1] is not None:
            st.warning("⚠️ Already punched in today!")
            return

        # Save photo
        filename = os.path.join(
            photos_dir,
            f"{emp_id}_{now.strftime('%Y%m%d_%H%M%S')}.jpg"
        )

        with open(filename, "wb") as f:
            f.write(st.session_state["captured_photo"].getbuffer())

        # Insert DB entry
        c.execute("""
            INSERT INTO attendance (emp_id, date, punch_in, work_hours, photo_path)
            VALUES (?, ?, ?, ?, ?)
        """, (
            emp_id,
            now.date().isoformat(),
            now.isoformat(),
            0,
            filename
        ))

        conn.commit()

        st.success("✅ Punch In Recorded Successfully")

    # -----------------------------------------------------------
    # ✅ PUNCH OUT
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
            return

        att_id, punch_in, punch_out = row

        if punch_out is not None:
            st.warning("⚠️ Already punched out today!")
            return

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
    # ✅ ATTENDANCE SUMMARY
    # -----------------------------------------------------------
    st.subheader("📅 Attendance Summary")

    df = pd.read_sql("""
        SELECT * FROM attendance WHERE emp_id=?
    """, conn, params=(emp_id,))

    st.dataframe(df, use_container_width=True)

    # -----------------------------------------------------------
    # ✅ WEEKLY & MONTHLY TOTALS
    # -----------------------------------------------------------
    if not df.empty:

        df["date"] = pd.to_datetime(df["date"], errors='coerce')
        df["work_hours"] = pd.to_numeric(df["work_hours"], errors='coerce').fillna(0)

        current_week = df[df["date"].dt.isocalendar().week == datetime.now().isocalendar().week]
        week_hours = current_week["work_hours"].sum()

        current_month = df[df["date"].dt.month == datetime.now().month]
        month_hours = current_month["work_hours"].sum()

        st.metric("🗓 This Week Hours", f"{week_hours:.2f} hrs")
        st.metric("📆 This Month Hours", f"{month_hours:.2f} hrs")

    else:
        st.info("No attendance data found.")
