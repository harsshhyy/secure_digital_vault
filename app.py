from flask import Flask, render_template, request, redirect, session, jsonify, send_file
import sqlite3
import os
import io
from datetime import datetime

from flask_bcrypt import Bcrypt
from cryptography.fernet import Fernet

# Project modules
from behaviour_ml_pipeline import BehaviourModel
from behaviour_dataset import BehaviourDataset

# -----------------------------
# Flask Setup
# -----------------------------
app = Flask(__name__)
app.secret_key = "vault_secret_key"
bcrypt = Bcrypt(app)

UPLOAD_FOLDER = "vault_files"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -----------------------------
# Encryption Key
# -----------------------------
if not os.path.exists("key.key"):
    key = Fernet.generate_key()
    with open("key.key", "wb") as f:
        f.write(key)

with open("key.key", "rb") as f:
    key = f.read()

cipher = Fernet(key)

# -----------------------------
# ML Components
# -----------------------------
behaviour_model = BehaviourModel()
behaviour_dataset = BehaviourDataset()
model_loaded = False
try:
    behaviour_model.load()
    model_loaded = True
    print("✅ Behaviour model loaded")
except Exception as e:
    print("⚠ No trained model found:", e)

# -----------------------------
# Database
# -----------------------------
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    conn = get_db()
    # USERS
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        email TEXT,
        password TEXT
    )
    """)
    # NOTES
    conn.execute("""
    CREATE TABLE IF NOT EXISTS notes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        content TEXT
    )
    """)
    # FILE METADATA
    conn.execute("""
    CREATE TABLE IF NOT EXISTS files(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        filename TEXT,
        tags TEXT
    )
    """)
    # BEHAVIOR LOGS
    conn.execute("""
    CREATE TABLE IF NOT EXISTS behavior_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        action TEXT,
        details TEXT,
        timestamp TEXT
    )
    """)
    conn.commit()
    conn.close()

create_table()

# -----------------------------
# Routes
# -----------------------------
@app.route("/")
def home():
    return redirect("/login")

# -----------------------------
# Register
# -----------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        hashed = bcrypt.generate_password_hash(password).decode("utf-8")
        conn = get_db()
        conn.execute(
            "INSERT INTO users(username,email,password) VALUES(?,?,?)",
            (username, email, hashed)
        )
        conn.commit()
        conn.close()
        return redirect("/login")
    return render_template("register.html")

# -----------------------------
# Login
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()
        conn.close()
        if user and bcrypt.check_password_hash(user["password"], password):
            session["user"] = user["username"]
            return redirect("/dashboard")
        return "Invalid login"
    return render_template("login.html")

# -----------------------------
# Dashboard
# -----------------------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    files = os.listdir(app.config["UPLOAD_FOLDER"])
    conn = get_db()
    file_data = conn.execute(
        "SELECT * FROM files WHERE user=?",
        (session["user"],)
    ).fetchall()
    conn.close()
    return render_template(
        "dashboard.html",
        user=session["user"],
        files=files,
        file_data=file_data
    )

# -----------------------------
# Logout
# -----------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# -----------------------------
# Upload File (Encrypted + Metadata)
# -----------------------------
# -----------------------------
# Upload File (Encrypted + Metadata)
# -----------------------------
@app.route("/upload", methods=["POST"])
def upload():
    if "user" not in session:
        return redirect("/login")

    file = request.files.get("file")
    custom_name = request.form.get("filename")
    tags = request.form.get("tags")

    if file and file.filename != "":
        # Use custom filename if provided
        filename = custom_name if custom_name else file.filename
        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

        data = file.read()
        encrypted = cipher.encrypt(data)

        with open(path, "wb") as f:
            f.write(encrypted)

        # ✅ Save metadata to DB
        conn = get_db()
        conn.execute(
            "INSERT INTO files(user, filename, tags) VALUES(?,?,?)",
            (session["user"], filename, tags)
        )
        conn.commit()
        conn.close()

    else:
        print("⚠ No file received")

    return redirect("/dashboard")

# -----------------------------
# Download File (Decrypted)
# -----------------------------
@app.route("/download/<filename>")
def download(filename):
    if "user" not in session:
        return redirect("/login")
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    with open(path, "rb") as f:
        encrypted = f.read()
    decrypted = cipher.decrypt(encrypted)
    return send_file(
        io.BytesIO(decrypted),
        download_name=filename,
        as_attachment=True
    )

# -----------------------------
# Save Note
# -----------------------------
@app.route("/save_note", methods=["POST"])
def save_note():
    if "user" not in session:
        return jsonify({"message": "Not logged in"})
    data = request.json
    note = data.get("note")
    encrypted_note = cipher.encrypt(note.encode())
    conn = get_db()
    conn.execute(
        "INSERT INTO notes(user, content) VALUES(?,?)",
        (session["user"], encrypted_note)
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Note saved securely!"})

# -----------------------------
# Get Notes
# -----------------------------
@app.route("/get_notes")
def get_notes():
    if "user" not in session:
        return jsonify({"notes": []})
    conn = get_db()
    rows = conn.execute(
        "SELECT content FROM notes WHERE user=?",
        (session["user"],)
    ).fetchall()
    conn.close()
    notes = [cipher.decrypt(r["content"]).decode() for r in rows]
    return jsonify({"notes": notes})

# -----------------------------
# Behaviour ML API
# -----------------------------
@app.route("/behaviour", methods=["POST"])
def behaviour():
    if "user" not in session:
        return jsonify({"status": "no_session", "action": "logout"})
    data = request.get_json()
    feature_vector = [
        data.get("typing_speed", 0),
        data.get("key_delay", 0),
        data.get("mouse_speed", 0),
        data.get("mouse_click_rate", 0),
        data.get("session_time", 0)
    ]
    if model_loaded:
        try:
            result = behaviour_model.predict(feature_vector)
        except:
            result = "normal"
    else:
        result = "normal"
    if result == "normal":
        behaviour_dataset.add_sample(feature_vector)
    if result == "anomaly":
        session.clear()
        return jsonify({"status": "anomaly", "action": "logout"})
    return jsonify({"status": "normal", "action": "ok"})

# -----------------------------
# Log Behavior
# -----------------------------
@app.route("/log_behavior", methods=["POST"])
def log_behavior():
    if "user" not in session:
        return jsonify({"status": "no_session"})
    data = request.get_json()
    action = data.get("action", "")
    details = str({k: v for k,v in data.items() if k != "action"})
    timestamp = datetime.now().isoformat()
    conn = get_db()
    conn.execute(
        "INSERT INTO behavior_logs(user, action, details, timestamp) VALUES(?,?,?,?)",
        (session["user"], action, details, timestamp)
    )
    conn.commit()
    conn.close()
    print(f"📌 Behavior Logged: {action} | {details}")
    return jsonify({"status": "ok"})

# -----------------------------
# Run App
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)