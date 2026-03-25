import streamlit as st
import os
from auth import verify_user, get_user_role
from database import init_db
import admin_dashboard
import employee_dashboard

# ------------------------------
# ✅ Initialize DB
# ------------------------------
init_db()

st.set_page_config(page_title="Attendance System", layout="wide")

# ------------------------------
# ✅ Ensure photos folder exists
# ------------------------------
if not os.path.exists("photos"):
    os.makedirs("photos")

# ------------------------------
# ✅ Session State Initialization
# ------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "role" not in st.session_state:
    st.session_state.role = None

if "emp_id" not in st.session_state:
    st.session_state.emp_id = None

# ------------------------------
# ✅ Hide Streamlit’s Sidebar (Removes Page Leakage)
# ------------------------------
hide_sidebar_style = """
<style>
    [data-testid="stSidebar"] {display: none;}
</style>
"""
st.markdown(hide_sidebar_style, unsafe_allow_html=True)


# ------------------------------
# ✅ Login Screen
# ------------------------------
def login_screen():
    st.title("📌 Attendance Management System")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        emp_id = verify_user(username, password)

        if emp_id:
            st.success("✅ Login Successful")

            st.session_state.logged_in = True
            st.session_state.emp_id = emp_id
            st.session_state.role = get_user_role(emp_id)

            st.rerun()   # ✅ Reload with session active
        else:
            st.error("❌ Invalid username or password!")


# ------------------------------
# ✅ Role-Based Secure Routing
# ------------------------------
if not st.session_state.logged_in:
    login_screen()

else:
    if st.session_state.role == "admin":
        admin_dashboard.show(st.session_state.emp_id)

    elif st.session_state.role == "employee":
        employee_dashboard.show(st.session_state.emp_id)

    else:
        st.error("❌ Unknown role! Contact admin.")