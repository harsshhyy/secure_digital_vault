from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
import os
from flask_bcrypt import Bcrypt
from cryptography.fernet import Fernet
from behaviour_model import predict

app = Flask(__name__)
app.secret_key = "vault_secret_key"

bcrypt = Bcrypt(app)

UPLOAD_FOLDER = "vault_files"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

key = Fernet.generate_key()
cipher = Fernet(key)


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


@app.route("/")
def home():
    return render_template("login.html")


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


@app.route("/logout")
def logout():

    session.pop("user", None)

    return redirect("/")


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


from flask import send_file
import io


@app.route("/download/<filename>")
def download(filename):

    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    with open(path, "rb") as f:
        encrypted_data = f.read()

    decrypted_data = cipher.decrypt(encrypted_data)

    return send_file(
        io.BytesIO(decrypted_data),
        download_name=filename,
        as_attachment=True
    )

@app.route("/behaviour", methods=["POST"])
def behaviour():

    data = request.get_json()

    typing_speed = data.get("typing_speed", 0)
    mouse_speed = data.get("mouse_speed", 0)

    result = predict(typing_speed, mouse_speed)

    return jsonify({"status": result})


if __name__ == "__main__":
    app.run(debug=True)