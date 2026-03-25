from flask import Flask, render_template, request, redirect, session, jsonify, send_file
import sqlite3
import os
import io

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

# Load trained model safely
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
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        email TEXT,
        password TEXT
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

    return render_template(
        "dashboard.html",
        user=session["user"],
        files=files
    )


# -----------------------------
# Logout
# -----------------------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# -----------------------------
# Upload File (Encrypted)
# -----------------------------

@app.route("/upload", methods=["POST"])
def upload():

    if "user" not in session:
        return redirect("/login")

    file = request.files.get("file")

    if file:
        data = file.read()
        encrypted = cipher.encrypt(data)

        path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            file.filename
        )

        with open(path, "wb") as f:
            f.write(encrypted)

    return redirect("/dashboard")


# -----------------------------
# Download File (Decrypted)
# -----------------------------

@app.route("/download/<filename>")
def download(filename):

    if "user" not in session:
        return redirect("/login")

    path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    with open(path, "rb") as f:
        encrypted = f.read()

    decrypted = cipher.decrypt(encrypted)

    return send_file(
        io.BytesIO(decrypted),
        download_name=filename,
        as_attachment=True
    )


# -----------------------------
# Behaviour Detection API (FINAL)
# -----------------------------

@app.route("/behaviour", methods=["POST"])
def behaviour():

    if "user" not in session:
        return jsonify({
            "status": "no_session",
            "action": "logout"
        })

    data = request.get_json()

    typing_speed = data.get("typing_speed", 0)
    key_delay = data.get("key_delay", 0)
    mouse_speed = data.get("mouse_speed", 0)
    mouse_click_rate = data.get("mouse_click_rate", 0)
    session_time = data.get("session_time", 0)

    feature_vector = [
        typing_speed,
        key_delay,
        mouse_speed,
        mouse_click_rate,
        session_time
    ]

    print("📊 Feature Vector:", feature_vector)

    # Predict safely
    if model_loaded:
        try:
            result = behaviour_model.predict(feature_vector)
        except Exception as e:
            print("Prediction error:", e)
            result = "normal"
    else:
        result = "normal"

    print("🧠 Prediction:", result)

    # Adaptive learning
    if result == "normal":
        behaviour_dataset.add_sample(feature_vector)

    # SECURITY ACTION
    if result == "anomaly":
        session.clear()
        return jsonify({
            "status": "anomaly",
            "action": "logout"
        })

    return jsonify({
        "status": "normal",
        "action": "ok"
    })


# -----------------------------
# Run App
# -----------------------------

if __name__ == "__main__":
    app.run(debug=True)