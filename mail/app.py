# WHO'S YOUR DADDY ?!

import os
from click import confirmation_option

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///mail.db")



@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response




# INDEX

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Show portfolio of stocks"""
    if request.method == "GET":
        user_id = session['user_id']
        rows = db.execute("SELECT * FROM informations WHERE user_id = ?", user_id)
        return render_template("index.html", rows=rows)
    
    # If delete account
    user_id = session['user_id']
    db.execute("DELETE FROM users WHERE id = ?", user_id)
    db.execute("DELETE FROM informations WHERE user_id = ?", user_id)
    
    # Turn to REGISTER
    return redirect("/login")



# LOG IN

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        if not username:
            message = 'Username required!'
            return render_template("login.html", message1=message)
        password = request.form.get("password")
        if not password:
            message = 'Password required!'
            return render_template("login.html", message2=message)

        # Check if user exists in database
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        if len(rows) == 0:
            message = 'User does not exist!'
            return render_template("login.html", message1=message)

        # Check password
        if not check_password_hash(rows[0]['hash'], password):
            message = 'Invalid password!'
            return render_template("login.html", message2=message)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        user_id = session['user_id']
        rows = db.execute("SELECT * FROM informations WHERE user_id = ?", user_id)
        if len(rows) == 0:
            # Redirect user to home page
            return render_template("information.html")
        return redirect("/")

    return render_template("login.html")



# LOG OUT

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")





# REGISTER

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        if not username:
            message = 'Must provide username!'
            return render_template("register.html", message1=message)
        password = request.form.get("password")
        if not password:
            message = 'Must provide password!'
            return render_template("register.html", message2=message)
        confirmation = request.form.get("confirmation")
        if not confirmation:
            message = 'Must confirm password!'
            return render_template("register.html", message3=message)

        # Check whether if username exists in database or not
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        if len(rows) != 0:
            message = 'User already exists!'
            return render_template("register.html", message1=message)

        if confirmation != password:
            message = 'Password confirmation not correct!'
            return render_template("register.html", message3=message)

        # hash password
        hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

        # Update database:
        try:
            db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, hash)
        except:
            message = 'User already exists!'
            return render_template("register.html", message1=message)

        # Redirect to homepage
        return render_template("login.html")

    return render_template("register.html")


# INFORMATION

@app.route("/information", methods=["GET", "POST"])
@login_required
def information():
    if request.method == "POST":
        name = request.form.get("name")
        if not name:
            message = 'Name required!'
            return render_template("information.html", message=message)
        birth = request.form.get("birth")
        place = request.form.get("place")
        number = request.form.get("number")
        email = request.form.get("email")

        # Update Informations
        user_id = session['user_id']
        db.execute("INSERT INTO informations (user_id, name, birth, place, number, email) VALUES(?, ?, ?, ?, ?, ?)", user_id, name, birth, place, number, email)

        # Turn back to index
        return redirect("/")

    return render_template("information.html")