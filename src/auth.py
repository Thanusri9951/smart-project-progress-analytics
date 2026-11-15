import streamlit as st
import sqlite3, hashlib, os
from pathlib import Path
DB=Path("data/app.db")

def _conn():
    DB.parent.mkdir(parents=True,exist_ok=True)
    return sqlite3.connect(DB)

def _hash(password,salt):
    return hashlib.pbkdf2_hmac("sha256",password.encode(),salt.encode(),180000).hex()

def init_db():
    with _conn() as c:
        c.execute("CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY,salt TEXT NOT NULL,password_hash TEXT NOT NULL,role TEXT NOT NULL)")
        c.execute("CREATE TABLE IF NOT EXISTS upload_log(id INTEGER PRIMARY KEY AUTOINCREMENT,filename TEXT,rows INTEGER,username TEXT,uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        c.execute("CREATE TABLE IF NOT EXISTS notes(id INTEGER PRIMARY KEY AUTOINCREMENT,project_id TEXT,note TEXT,username TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        exists=c.execute("SELECT username FROM users WHERE username='admin'").fetchone()
        if not exists:
            salt=os.urandom(16).hex()
            c.execute("INSERT INTO users VALUES(?,?,?,?)",("admin",salt,_hash("Admin@123",salt),"admin"))

def verify(username,password):
    with _conn() as c:
        row=c.execute("SELECT salt,password_hash,role FROM users WHERE username=?",(username,)).fetchone()
    if not row: return None
    return row[2] if _hash(password,row[0])==row[1] else None

def login_form():
    with st.form("login"):
        st.subheader("Sign in")
        username=st.text_input("Username")
        password=st.text_input("Password",type="password")
        ok=st.form_submit_button("Login",use_container_width=True)
    if ok:
        role=verify(username.strip(),password)
        if role:
            st.session_state.authenticated=True
            st.session_state.username=username.strip()
            st.session_state.role=role
            st.rerun()
        else: st.error("Invalid username or password.")
    st.info("Demo administrator: username `admin` · password `Admin@123`. Change this before public deployment.")

def logout():
    for key in ["authenticated","username","role","dataset","dataset_name"]:
        st.session_state.pop(key,None)

def is_admin(username):
    with _conn() as c:
        row=c.execute("SELECT role FROM users WHERE username=?",(username,)).fetchone()
    return bool(row and row[0]=="admin")
