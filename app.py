from flask import Flask, render_template, request, redirect, session, jsonify, send_file
import sqlite3
import os
import io

from flask_bcrypt import Bcrypt
from cryptography.fernet import Fernet

import numpy as np

# Project modules
from behaviour_ml_pipeline import BehaviourModel
from behaviour_dataset import BehaviourDataset

# Flask Setup

app = Flask(__name__)
app.secret_key = "vault_secret_key"

bcrypt = Bcrypt(app)

# Upload folder
UPLOAD_FOLDER = "vault_files"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Ensure folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -----------------------------
# Encryption Key
# -----------------------------

# Prototype project uses runtime key
key = Fernet.generate_key()
cipher = Fernet(key)


# ML Components


behaviour_model = BehaviourModel()
behaviour_dataset = BehaviourDataset()

# Load trained model if exists
try:
    behaviour_model.load()
    print("Behaviour model loaded")
except:
    print("New behaviour model instance")

# Database Connection

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# Create User Table

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

# Routes

@app.route("/")
def home():
    return render_template("login.html")

# Register

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        conn = get_db()

        conn.execute(
            "INSERT INTO users(username,email,password) VALUES(?,?,?)",
            (username, email, hashed_password)
        )

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("register.html")

# Login

@app.route("/login", methods=["POST"])
def login():

    email = request.form["email"]
    password = request.form["password"]

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE email=?", (email,)
    ).fetchone()

    conn.close()

    if user and bcrypt.check_password_hash(user["password"], password):

        session["user"] = user["username"]

        return redirect("/dashboard")

    return "Invalid Login"

# Dashboard

@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/")

    files = os.listdir(app.config["UPLOAD_FOLDER"])

    return render_template(
        "dashboard.html",
        user=session["user"],
        files=files
    )


# Logout

@app.route("/logout")
def logout():

    session.pop("user", None)
    return redirect("/")

# Upload File

@app.route("/upload", methods=["POST"])
def upload():

    if "user" not in session:
        return redirect("/")

    file = request.files["file"]

    if file:

        data = file.read()

        encrypted_data = cipher.encrypt(data)

        path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)

        with open(path, "wb") as f:
            f.write(encrypted_data)

    return redirect("/dashboard")

# Download File

@app.route("/download/<filename>")
def download(filename):

    if "user" not in session:
        return redirect("/")

    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    with open(path, "rb") as f:
        encrypted_data = f.read()

    decrypted_data = cipher.decrypt(encrypted_data)

    return send_file(
        io.BytesIO(decrypted_data),
        download_name=filename,
        as_attachment=True
    )

# Behaviour Prediction API

@app.route("/behaviour", methods=["POST"])
def behaviour():

    data = request.get_json()

    typing_speed = data.get("typing_speed", 0)
    mouse_speed = data.get("mouse_speed", 0)

    feature_vector = [
        typing_speed,
        mouse_speed
    ]

    result = behaviour_model.predict(feature_vector)

    # Adaptive learning buffer
    if result == "normal":
        behaviour_dataset.add_sample(feature_vector)

    return jsonify({
        "status": result
    })


if __name__ == "__main__":
    app.run(debug=True)