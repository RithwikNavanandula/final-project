import os
import subprocess

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from flask_uploads import UploadSet, configure_uploads
from helpers import login_required, save_video, compress_video

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure uploads
media = UploadSet('media', extensions=('mp4',))
configure_uploads(app, media)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///videos.db")

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
@login_required
def index():
    """Show portfolio of symbols"""
    user_id = session["user_id"]
    original = db.execute("SELECT original_path FROM videos WHERE user_id = ?", user_id)  
    compressed = db.execute("SELECT compressed_path FROM videos WHERE user_id = ?", user_id)
    return render_template("index.html", original=original, compressed=compressed)

@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    user_id = session["user_id"]
    num_videos = db.execute("SELECT COUNT(video_id) FROM videos WHERE user_id = ?", user_id)
    if request.method == "GET":
        return render_template("upload.html")
    else:
        if "video" in request.files:
            video = request.files["video"]
            if video.filename == "":
                flash("No file selected")
                return redirect(request.url)
            if video and allowed_file(video.filename):
                filename = secure_filename(video.filename)
                media.save(video, name=filename)
                flash("File uploaded successfully")
                return redirect("/")
            else:
                flash("Invalid file type")
                return redirect(request.url)
        else:
            flash("No video found in request")
            return redirect(request.url)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    session.clear()  # Forget any user_id

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            flash("Must provide username")
            return redirect("/login")
        elif not password:
            flash("Must provide password")
            return redirect("/login")

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            flash("Invalid username and/or password")
            return redirect("/login")

        session["user_id"] = rows[0]["id"]
        return redirect("/")
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""
    session.clear()  # Forget any user_id
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            return redirect("/register")
        if not password:
            return redirect("/register")
        if not confirmation:
            return redirect("/register")
        if password != confirmation:
            return redirect("/register")

        hash = generate_password_hash(password)

        try:
            new_user = db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash)
        except:
            return redirect("Username already exists")

        session["user_id"] = new_user
        return redirect("/")

@app.route("/password", methods=["GET", "POST"])
@login_required
def password():
    if request.method == "GET":
        return render_template("password.html")
    else:
        oldpassword = request.form.get("oldpassword")
        newpassword = request.form.get("newpassword")
        confirmation = request.form.get("confirmation")

        hash = db.execute("SELECT hash FROM users WHERE id = ?", session["user_id"])

        if not check_password_hash(hash[0]["hash"], oldpassword):
            flash("Incorrect current password")
            return redirect("/password")
        elif not newpassword:
            flash("Must provide new password")
            return redirect("/password")
        elif not confirmation:
            flash("Must provide confirmation")
            return redirect("/password")
        elif newpassword != confirmation:
            flash("Passwords do not match")
            return redirect("/password")

        hash_final = generate_password_hash(newpassword)

        db.execute("UPDATE users SET hash = ? WHERE id = ?", hash_final, session["user_id"])

        flash("Password Updated")
        return redirect("/logout")
