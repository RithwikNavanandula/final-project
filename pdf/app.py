import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import datetime


app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///videos.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html")
    else:
        return render_template("index.html")
        

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            flash("must provide username", 403)
            return redirect("/login")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("must provide password", 403)
            return redirect("/login")

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            flash("invalid username and/or pass")
            return redirect("/login")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")
    
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
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
            flash("Must Give Username")
            return redirect("")  
        if not password:
            flash("Must Give Password")
            return redirect("")  
        if not confirmation:
            flash("Must Give Confirmation")
            return redirect("")      
        if password != confirmation:
            flash("Password Do Not Match")
            return redirect("")     
        hash = generate_password_hash(password)

        try:
            new_user = db.execute(
                "INSERT INTO users (username, hash) VALUES (?, ?)", username, hash
            )
        except:
            flash("Username already exists")
            return redirect("") 
             
        session["user_id"] = new_user

        return redirect("/")

@app.route("/upload", methods=["GET", "POST"])
def upload():
        if request.method == "GET":
            return render_template("upload.html")
        else:
            return render_template("upload.html")


