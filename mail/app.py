# WHO'S YOUR DADDY ?!

import os
from click import confirmation_option

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required

import datetime

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
        password = request.form.get("password")

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
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Check whether if username exists in database or not
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        if len(rows) != 0:
            message = 'User already exists!'
            return render_template("register.html", message1=message)

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
        user_id = session['user_id']

        name = request.form.get("name")
        birth = request.form.get("birth")
        place = request.form.get("place")
        number = request.form.get("number")
        email = request.form.get("email")
        
        db.execute("DELETE FROM informations WHERE user_id = ?", user_id)

        # Update Informations
        try:
            db.execute("INSERT INTO informations (user_id, name, birth, place, number, email) VALUES(?, ?, ?, ?, ?, ?)", user_id, name, birth, place, number, email)
        except:
            message = 'Invalid email (email already exists)!'
            return render_template("information.html", message=message)

        # Turn back to index
        return redirect("/")

    return render_template("information.html")



# FIND FRIEND AND SEND EMAIL

@app.route("/send", methods=["GET", "POST"])
@login_required
def send():
    if request.method == "POST":

        # Find friend
        receiver = request.form.get("receiver")

        user_names = db.execute("SELECT name FROM informations")
        names = []
        for row in user_names:
            names.append(row['name'])
        if receiver not in names:
            message = 'Name does not exist!'
            return render_template("send.html", message1=message)
        
        email = request.form.get("email")

        user_emails = db.execute("SELECT email FROM informations")
        emails = []
        for row in user_emails:
            emails.append(row['email'])
        if email not in emails:
            message = 'Email does not exist!'
            return render_template("send.html", message2=message)

        mail = request.form.get("mail")

        # IF NAME AND EMAIL DON'T MATCH
        receiver_emails = db.execute("SELECT email FROM informations WHERE name = ?", receiver)
        emails = []
        for row in receiver_emails:
            emails.append(row['email'])
        if email not in emails:
            message = "Name and Email don't match!"
            return render_template("send.html", message2=message)

        # IF user mails for themselves:
        sender_id = session['user_id']
        sender_email = db.execute("SELECT email FROM informations WHERE user_id = ?", sender_id)[0]['email']
        if email == sender_email:
            message = "You cannot mail for yourself!"
            return render_template("send.html", message4=message)

        receiver_id = db.execute("SELECT user_id FROM informations WHERE email = ?", email)[0]['user_id']
        sender = db.execute("SELECT name FROM informations WHERE user_id = ?", sender_id)[0]['name']
        receiver = db.execute("SELECT name FROM informations WHERE user_id = ?", receiver_id)[0]['name']
        date = datetime.datetime.now()

        db.execute("INSERT INTO mail_box (sender_id, receiver_id, sender, receiver, date, mail) VALUES (?, ?, ?, ?, ?, ?)", sender_id, receiver_id, sender, receiver, date, mail)
        return redirect("/send")

    return render_template("send.html")


# CHECK MAIL
@app.route("/mail")
@login_required
def mail():

    # Get informations from mail_box
    user_id = session['user_id']
    mails_received = db.execute("SELECT * FROM mail_box WHERE receiver_id = ?", user_id)

    mails = []
    
    for row in mails_received:
        value = {}
        value['sender'] = row['sender']
        value['email'] = db.execute("SELECT email FROM informations WHERE user_id = ?", row['sender_id'])[0]['email']
        value['mail'] = row['mail']
        value['date'] = row['date']
        mails.append(value)
    
    return render_template("mail.html", mails=mails)



# CHECK HISTORY
@app.route("/history")
@login_required
def history():
    user_id = session['user_id']
    rows = db.execute("SELECT * FROM mail_box WHERE sender_id = ? OR receiver_id = ?", user_id, user_id)
    
    histories = []

    for row in rows:
        history = {}
        history['sender'] = row['sender']
        history['sender_email'] = db.execute("SELECT email FROM informations WHERE user_id = ?", row['sender_id'])[0]['email']
        history['receiver'] = row['receiver']
        history['receiver_email'] = db.execute("SELECT email FROM informations WHERE user_id = ?", row['receiver_id'])[0]['email']
        history['mail'] = row['mail']
        history['date'] = row['date']
        histories.append(history)

    return render_template("history.html", histories=histories)



# CHANGE INFORMATION
@app.route("/change_information")
@login_required
def change_information():
    return render_template("information.html")