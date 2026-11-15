from src.auth import _conn

def save_upload_log(filename,rows,username):
    with _conn() as c:
        c.execute("INSERT INTO upload_log(filename,rows,username) VALUES(?,?,?)",(filename,rows,username))

def get_upload_history():
    with _conn() as c:
        return c.execute("SELECT filename,rows,username,uploaded_at FROM upload_log ORDER BY id DESC LIMIT 100").fetchall()

def add_project_note(project_id,note,username):
    with _conn() as c:
        c.execute("INSERT INTO notes(project_id,note,username) VALUES(?,?,?)",(project_id,note,username))

def get_project_notes(project_id):
    with _conn() as c:
        return c.execute("SELECT created_at,username,note FROM notes WHERE project_id=? ORDER BY id DESC",(project_id,)).fetchall()
