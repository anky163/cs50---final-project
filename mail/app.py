# WHO'S YOUR DADDY ?!

import os
from unittest.main import MAIN_EXAMPLES
from xml.dom import NotFoundErr
from click import confirmation_option

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required, check_valid_datetime, information_required

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


""" REQUIRE USER'S INFORMATION BEFORE ACCESSING ANY SITE
def information_required():
    user_id = session['user_id']
    rows = db.execute("SELECT * FROM informations WHERE user_id = ?", user_id)
    if len(rows) == 0:
        message = 'You must provide you informations first!'
        return render_template("information.html", requirement=message) """


# INDEX

@app.route("/", methods=["GET", "POST"])
@login_required
@information_required
def index():
    """Show portfolio of stocks"""
    if request.method == "GET":
        # REQUIRE USER'S INFORMATION BEFORE ACCESSING ANY SITE
        user_id = session['user_id']
        rows = db.execute("SELECT * FROM informations WHERE user_id = ?", user_id)

        return render_template("index.html", rows=rows)
    
    # DELETE ACCOUNT
    user_id = session['user_id']
    db.execute("DELETE FROM users WHERE id = ?", user_id)
    db.execute("DELETE FROM informations WHERE user_id = ?", user_id)
    db.execute("DELETE FROM mail_box WHERE sender_id = ? OR receiver_id = ?", user_id, user_id)
    db.execute("DELETE FROM friends WHERE host_id = ? OR friend_id = ?", user_id, user_id)
    # Then update table 'database'
    number_of_users = int(db.execute("SELECT COUNT(username) AS count FROM users")[0]['count'])
    number_of_mails = int(db.execute("SELECT COUNT(mail) AS count FROM mail_box")[0]['count'])
   
    db.execute("UPDATE database SET seq = ? WHERE name = 'users' OR name = 'informations'", number_of_users)
    db.execute("UPDATE database SET seq = ? WHERE name = 'mail_box'", number_of_mails)

    
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

        # Update table 'database'
        number_of_users = db.execute("SELECT COUNT(username) AS count FROM users")[0]['count']
        number_of_users = int(number_of_users)
        db.execute("UPDATE database SET seq = ? WHERE name = 'users' OR name = 'informations'", number_of_users)

        # Redirect to homepage
        return render_template("login.html")

    return render_template("register.html")



# SENDING EMAIL

@app.route("/sent", methods=["GET", "POST"])
@login_required
@information_required
def sent():
    if request.method == "POST":

        # Find friend
        receiver = request.form.get("receiver")

        user_names = db.execute("SELECT name FROM informations")
        names = []
        for row in user_names:
            names.append(row['name'])
        if receiver not in names:
            message = 'Name does not exist!'
            return render_template("sent.html", message1=message)
        
        email = request.form.get("email")

        user_emails = db.execute("SELECT email FROM informations")
        emails = []
        for row in user_emails:
            emails.append(row['email'])
        if email not in emails:
            message = 'Email does not exist!'
            return render_template("sent.html", message2=message)

        mail = request.form.get("mail")

        # IF NAME AND EMAIL DON'T MATCH
        receiver_emails = db.execute("SELECT email FROM informations WHERE name = ?", receiver)
        emails = []
        for row in receiver_emails:
            emails.append(row['email'])
        if email not in emails:
            message = "Name and Email don't match!"
            return render_template("sent.html", message2=message)

        # IF user mails for themselves:
        sender_id = session['user_id']
        sender_email = db.execute("SELECT email FROM informations WHERE user_id = ?", sender_id)[0]['email']
        if email == sender_email:
            message = "You cannot mail for yourself!"
            return render_template("sent.html", message4=message)

        receiver_id = db.execute("SELECT user_id FROM informations WHERE email = ?", email)[0]['user_id']
        sender = db.execute("SELECT name FROM informations WHERE user_id = ?", sender_id)[0]['name']
        receiver = db.execute("SELECT name FROM informations WHERE user_id = ?", receiver_id)[0]['name']
        date = datetime.datetime.now()

        db.execute("INSERT INTO mail_box (sender_id, receiver_id, sender, receiver, date, mail) VALUES (?, ?, ?, ?, ?, ?)", sender_id, receiver_id, sender, receiver, date, mail)
        number_of_mails = db.execute("SELECT COUNT(mail) AS count FROM mail_box")[0]['count']
        number_of_mails = int(number_of_mails) 
        db.execute("UPDATE database SET seq = ? WHERE name = 'mail_box'", number_of_mails)
        return redirect("/sent")


    user_id = session['user_id']

    rows = db.execute("SELECT * FROM mail_box WHERE sender_id = ? ORDER BY date DESC", user_id)
    mails = []
    for row in rows:
        mail = {}
        mail['receiver'] = row['receiver']
        receiver_id = row['receiver_id']
        mail['email'] = db.execute("SELECT email FROM informations WHERE user_id = ?", receiver_id)[0]['email']
        mail['mail'] = row['mail']
        mail['date'] = row['date']
        mails.append(mail)
    return render_template("sent.html", mails=mails)

# SEARCH SENT MAILS IN sent.html
@app.route("/search_sent", methods=["GET", "POST"])
@login_required
def search_sent():
    if request.method == "POST":
        user_id = session['user_id']
        rows = []

        name = request.form.get('name')
        if not name:
            message = "Name required!"
            return render_template("sent.html", name=message)
        receiver_email = request.form.get('receiver_email')
        date = request.form.get('date')
        if date:
            if check_valid_datetime(date) == False:
                message = 'Invalid date'
                return render_template("sent.html", date=message)
            date = '%' + date + '%'

        # Check if name exists or not
        user_names = db.execute("SELECT name FROM informations")
        names = []
        for row in user_names:
            names.append(row['name'])
        if name not in names:
            message = 'Name does not exist!'
            return render_template("sent.html", name=message)
        

        # If user did input receiver's email
        if receiver_email:
            email = db.execute("SELECT email FROM informations WHERE name = ? AND email = ?", name, receiver_email)
            # If name and email do not match
            if len(email) == 0:
                message = "Name and Email don't match!"
                return render_template("sent.html", email=message)
            receiver_id = db.execute("SELECT user_id FROM informations WHERE email = ?", receiver_email)[0]['user_id']
            if not date:
                rows = db.execute("SELECT * FROM mail_box WHERE sender_id = ? AND receiver = ? AND receiver_id = ? ORDER BY date DESC", user_id, name, receiver_id)
            else: 
                rows = db.execute("SELECT * FROM mail_box WHERE sender_id = ? AND receiver = ? AND receiver_id = ? AND date LIKE ? ORDER BY date DESC", user_id, name, receiver_id, date)
        # If user did not input receiver's email
        else:
            if date:
                rows = db.execute("SELECT * FROM mail_box WHERE sender_id = ? AND receiver = ? AND date LIKE ? ORDER BY date DESC", user_id, name, date)

  
        # If user only type receiver's name
        if not receiver_email and not date:
            rows = db.execute("SELECT * FROM mail_box WHERE sender_id = ? AND receiver = ? ORDER BY date DESC", user_id, name)

        if len(rows) == 0:
            message = "Not found!"
            return render_template("sent.html", notfound=message)

        mails = []
        for row in rows:
            mail = {}
            mail['receiver'] = row['receiver']
            receiver_id = row['receiver_id']
            mail['email'] = db.execute("SELECT email FROM informations WHERE user_id = ?", receiver_id)[0]['email']
            mail['mail'] = row['mail']
            mail['date'] = row['date']
            mails.append(mail)
        return render_template("sent.html", mails=mails)
    return redirect("/sent")


# CHECK INBOX

@app.route("/inbox")
@login_required
@information_required
def inbox():

    user_id = session['user_id']

    rows = db.execute("SELECT * FROM mail_box WHERE receiver_id = ? ORDER BY date DESC", user_id)
    mails = []
    for row in rows:
        mail = {}
        mail['sender'] = row['sender']
        sender_id = row['sender_id']
        mail['email'] = db.execute("SELECT email FROM informations WHERE user_id = ?", sender_id)[0]['email']
        mail['mail'] = row['mail']
        mail['date'] = row['date']
        mails.append(mail)
    return render_template("inbox.html", mails=mails)


# SEARCH INBOX IN inbox.html
@app.route("/search_inbox", methods=["GET", "POST"])
@login_required
@information_required
def search_inbox():
    if request.method == "POST":
        user_id = session['user_id']
        rows = []

        name = request.form.get('name')
        if not name:
            message = "Name required!"
            return render_template("inbox.html", name=message)
        sender_email = request.form.get('sender_email')
        date = request.form.get('date')

        if date:
            if check_valid_datetime(date) == False:
                message = 'Invalid date'
                return render_template("inbox.html", date=message)
            date = '%' + date + '%'

        # Check if name exists or not
        user_names = db.execute("SELECT name FROM informations")
        names = []
        for row in user_names:
            names.append(row['name'])
        if name not in names:
            message = 'Name does not exist!'
            return render_template("inbox.html", name=message)
        

        # If user did input receiver's email
        if sender_email:
            email = db.execute("SELECT email FROM informations WHERE name = ? AND email = ?", name, sender_email)
            # If name and email do not match
            if len(email) == 0:
                message = "Name and Email don't match!"
                return render_template("inbox.html", email=message)
            sender_id = db.execute("SELECT user_id FROM informations WHERE email = ?", sender_email)[0]['user_id']
            if not date:
                rows = db.execute("SELECT * FROM mail_box WHERE receiver_id = ? AND sender = ? AND sender_id = ? ORDER BY date DESC", user_id, name, sender_id)
            else: 
                rows = db.execute("SELECT * FROM mail_box WHERE receiver_id = ? AND sender = ? AND sender_id = ? AND date LIKE ? ORDER BY date DESC", user_id, name, sender_id, date)
        # If user did not input receiver's email
        else:
            if date:
                rows = db.execute("SELECT * FROM mail_box WHERE receiver_id = ? AND sender = ? AND date LIKE ? ORDER BY date DESC", user_id, name, date)

  
        # If user only type receiver's name
        if not sender_email and not date:
            rows = db.execute("SELECT * FROM mail_box WHERE receiver_id = ? AND sender = ? ORDER BY date DESC", user_id, name)

        if len(rows) == 0:
            message = "Not found!"
            return render_template("inbox.html", notfound=message)

        mails = []
        for row in rows:
            mail = {}
            mail['sender'] = row['sender']
            sender_id = row['sender_id']
            mail['email'] = db.execute("SELECT email FROM informations WHERE user_id = ?", sender_id)[0]['email']
            mail['mail'] = row['mail']
            mail['date'] = row['date']
            mails.append(mail)
        return render_template("inbox.html", mails=mails)
    return redirect("/inbox")



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
        # Check if email is valid or not
        emails = []
        rows = db.execute("SELECT email FROM informations WHERE NOT user_id = ?", user_id)
        for row in rows:
            emails.append(row['email'])
        if email in emails:
            message = 'Invalid email (email already exists)!'
            return render_template("information.html", message=message)
        
        db.execute("DELETE FROM informations WHERE user_id = ?", user_id)

        # Update Informations
        db.execute("INSERT INTO informations (user_id, name, birth, place, number, email) VALUES(?, ?, ?, ?, ?, ?)", user_id, name, birth, place, number, email)
        # Update Mail box
        db.execute("UPDATE mail_box SET sender = ? WHERE sender_id = ?", name, user_id)
        db.execute("UPDATE mail_box SET receiver = ? WHERE receiver_id = ?", name, user_id)
        # Turn back to index
        return redirect("/")

    return render_template("information.html")



# CHANGE INFORMATION
@app.route("/change_information")
@login_required
def change_information():
    # REQUIRE USER'S INFORMATION BEFORE ACCESSING ANY SITE
    user_id = session['user_id']
    rows = db.execute("SELECT * FROM informations WHERE user_id = ?", user_id)
    if len(rows) == 0:
        message = 'You must provide you informations first!'
        return render_template("information.html", requirement=message)
    return render_template("information.html")



# CHANGE PASSWORD
@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    
    if request.method == "GET":
        return render_template("change_password.html")

    oldPassword = request.form.get('oldPassword')
    newPassword = request.form.get('newPassword')

    user_id = session['user_id']
    hash = db.execute("SELECT hash FROM users WHERE id = ?", user_id)[0]['hash']

    if not check_password_hash(hash, oldPassword):
        message = 'Invalid password!'
        return render_template("change_password.html", message1=message)

    newPassword = generate_password_hash(newPassword, method='pbkdf2:sha256', salt_length=8)
    # Update users database
    db.execute("UPDATE users SET hash = ? WHERE id = ?", newPassword, user_id)
    success = 'Changing password successed!'
    return render_template("change_password.html", success=success)

    

# FINDING PEOPLE
@app.route("/find", methods = ["GET", "POST"])
@login_required
@information_required
def find():
    if request.method == "GET":
        user_id = session['user_id']

        rows = db.execute("SELECT * FROM informations WHERE NOT user_id = ? ORDER BY name", user_id)

        people = []

        for row in rows:
            person = {}

            person['name'] = row['name']
            person['email'] = row['email']
            person['birth'] = row['birth']
            person['place'] = row['place']
            person['number'] = row['number']
          
            person_id = db.execute("SELECT user_id FROM informations WHERE email = ?", person['email'])[0]['user_id']

            row = db.execute("SELECT * FROM friends WHERE host_id = ? AND friend_id = ? OR host_id = ? AND friend_id = ?", user_id, person_id, person_id, user_id)
            if len(row) == 0:
                person['operation'] = 'Add friend'
            else:
                # Accept request || Cancel request || Unfriend

                if row[0]['status'] == 'unconfirmed':
                    # If person is host
                    if user_id == row[0]['friend_id']:
                        person['operation'] = 'Accept'
                    # If user is host
                    if user_id == row[0]['host_id']:
                        person['operation'] = 'Cancel request'
                elif row[0]['status'] == 'confirmed':
                    person['operation'] = 'Unfriend'

            people.append(person)
        return render_template("find.html", people=people)

    
    # Find people
    user_id = session['user_id']
    name = request.form.get("name")
    email = request.form.get("email")

    name = '%' + name + '%'
    email = '%' + email + '%'

    rows = []
    if not name:
        rows = db.execute("SELECT * FROM informations WHERE email LIKE ? ORDER BY name", email)
    if not email:
        rows = db.execute("SELECT * FROM informations WHERE name LIKE ? ORDER BY name", name)
    if name and email:
        rows = db.execute("SELECT * FROM informations WHERE name LIKE ? AND email LIKE ? ORDER BY name", name, email)

    if len(rows) == 0:
        message = 'Not found!'
        return render_template("find.html", message=message)

    people = []
    for row in rows:
        person = {}
        person['name'] = row['name']
        person['email'] = row['email']
        person['birth'] = row['birth']
        person['place'] = row['place']
        person['number'] = row['number']

        person_id = db.execute("SELECT user_id FROM informations WHERE email = ?", person['email'])[0]['user_id']

        row = db.execute("SELECT * FROM friends WHERE host_id = ? AND friend_id = ? OR host_id = ? AND friend_id = ?", user_id, person_id, person_id, user_id)
        if len(row) == 0:
            person['operation'] = 'Add friend'
        else:
            # Accept request || Cancel request || Unfriend
            if row[0]['status'] == 'unconfirmed':
                # If person is host
                if user_id == row[0]['friend_id']:
                    person['operation'] = 'Accept'
                # If user is host
                if user_id == row[0]['host_id']:
                    person['operation'] = 'Cancel request'
            elif row[0]['status'] == 'confirmed':
                person['operation'] = 'Unfriend'

        people.append(person)
    return render_template("find.html", people=people)



# ADD FRIEND
@app.route("/add", methods=["POST"])
@login_required
def add():
    user_id = session['user_id']
    name = request.form.get("name")
    email = request.form.get("email")

    person_id = db.execute("SELECT user_id FROM informations WHERE email = ?", email)[0]['user_id']

    row = db.execute("SELECT * FROM friends WHERE host_id = ? AND friend_id = ? OR host_id = ? AND friend_id = ?", user_id, person_id, person_id, user_id)

    # Add friend
    if len(row) == 0:
        db.execute("INSERT INTO friends (host_id, friend_id, status) VALUES (?, ?, ?)", user_id, person_id, 'unconfirmed')
        return redirect("/list")

    # Accept request
    if user_id == row[0]['friend_id']:
        if row[0]['status'] == 'unconfirmed':
            db.execute("UPDATE friends SET status = ? WHERE host_id = ? AND friend_id = ?", 'confirmed', person_id, user_id)

    # Cancel request
    if user_id == row[0]['host_id']:
        if row[0]['status'] == 'unconfirmed':
            db.execute("DELETE FROM friends WHERE host_id = ? AND friend_id = ?", user_id, person_id)

    # Unfriend
    if row[0]['status'] == 'confirmed':
        db.execute("DELETE FROM friends WHERE host_id = ? AND friend_id = ? OR host_id = ? AND friend_id = ?", user_id, person_id, person_id, user_id)

    return redirect("/list")

# FRIEND LIST
@app.route("/list", methods=["GET", "POST"])
@login_required
@information_required
def list():
    user_id = session['user_id']
    if request.method == "GET":
        # Select people that are friends, OR unapprove friends, OR people sent requests
        rows = db.execute("SELECT * FROM informations JOIN friends ON user_id = host_id OR user_id = friend_id WHERE host_id = ? OR friend_id = ?", user_id, user_id)

        people = []

        for row in rows:
            if user_id != row['user_id']:
                person = {}
                person['name'] = row['name']
                person['email'] = row['email']
                person['birth'] = row['birth']
                person['place'] = row['place']
                person['number'] = row['number']

                # If already friends
                if row['status'] == 'confirmed':
                    person['operation'] = 'Unfriend'

                # If unapprove friends
                if user_id == row['host_id'] and row['status'] == 'unconfirmed':
                    person['operation'] = 'Cancel request'

                # If that person is the one who sent request
                if user_id == row['friend_id'] and row['status'] == 'unconfirmed':
                    person['operation'] = 'Accept'

                people.append(person)
        return render_template("list.html", people=people)

    
    # Query friend list
    name = request.form.get("name")
    email = request.form.get("email")
    name = '%' + name + '%'
    if email:
        email = '%' + email + '%'
    rows = []

    if not email:
        rows = db.execute("SELECT user_id FROM informations WHERE name LIKE ?", name)

    if email:
        rows = db.execute("SELECT user_id FROM informations WHERE name LIKE ? AND email LIKE ?", name, email)

    if len(rows) == 0:
        message = 'Not found!'
        return render_template("list.html", message=message)

    # Check if that person in friend list or not

    if not email:
        rows = db.execute("SELECT * FROM informations JOIN friends ON user_id = host_id OR user_id = friend_id WHERE host_id = ? AND friend_id IN (SELECT user_id FROM informations WHERE name LIKE ?) OR host_id IN (SELECT user_id FROM informations WHERE name LIKE ?) AND friend_id = ?", user_id, name, name, user_id)

    if email:
        rows = db.execute("SELECT * FROM informations JOIN friends ON user_id = host_id OR user_id = friend_id WHERE host_id = ? AND friend_id IN (SELECT user_id FROM informations WHERE name LIKE ? AND email LIKE ?) OR host_id IN (SELECT user_id FROM informations WHERE name LIKE ? AND email LIKE ?) AND friend_id = ?", user_id, name, email, name, email, user_id)

    if len(rows) == 0:
        message = 'Not found!'
        return render_template("list.html", message=message)

    people = []
    for row in rows:
        if user_id != row['user_id']:
            person = {}
            person['name'] = row['name']
            person['email'] = row['email']
            person['birth'] = row['birth']
            person['place'] = row['place']
            person['number'] = row['number']


            # If already friends
            if row['status'] == 'confirmed':
                person['operation'] = 'Unfriend'

            # If unapprove friends
            if user_id == row['host_id'] and row['status'] == 'unconfirmed':
                person['operation'] = 'Cancel request'

            # If that person is the one who sent request
            if user_id == row['friend_id'] and row['status'] == 'unconfirmed':
                person['operation'] = 'Accept'

            people.append(person)
    return render_template("list.html", people=people)



# FRIEND REQUESTS
@app.route("/requests", methods=["GET", "POST"])
@login_required
@information_required
def requests():
    user_id = session['user_id']
    if request.method == "GET":
        # Select all people that sent requests to user BUT user has not accepted yet
        rows = db.execute("SELECT * FROM informations JOIN friends ON user_id = host_id WHERE friend_id = ? AND status = ?", user_id, 'unconfirmed')
        people = []
        for row in rows:
            person = {}
            person['name'] = row['name']
            person['email'] = row['email']
            person['birth'] = row['birth']
            person['place'] = row['place']
            person['number'] = row['number']
            person['operation'] = 'Accept'

            people.append(person)

        return render_template("requests.html", people=people)

    
    # COPY from "/list"
       # Query friend list
    name = request.form.get("name")
    email = request.form.get("email")
    name = '%' + name + '%'
    if email:
        email = '%' + email + '%'
    rows = []

    if not email:
        rows = db.execute("SELECT user_id FROM informations WHERE name LIKE ?", name)

    if email:
        rows = db.execute("SELECT user_id FROM informations WHERE name LIKE ? AND email LIKE ?", name, email)

    if len(rows) == 0:
        message = 'Not found!'
        return render_template("list.html", message=message)

    # Check if that person sent you request or not

    if not email:
        rows = db.execute("SELECT * FROM informations JOIN friends ON user_id = host_id WHERE host_id IN (SELECT user_id FROM informations WHERE name LIKE ?) AND friend_id = ? AND status = ?", name, user_id, 'unconfirmed')

    if email:
        rows = db.execute("SELECT * FROM informations JOIN friends ON user_id = host_id WHERE host_id IN (SELECT user_id FROM informations WHERE name LIKE ? AND email LIKE ?) AND friend_id = ? AND status = ?", name, email, user_id, 'unconfirmed')

    if len(rows) == 0:
        message = 'Not found!'
        return render_template("list.html", message=message)

    people = []
    for row in rows:
        person = {}
        person['name'] = row['name']
        person['email'] = row['email']
        person['birth'] = row['birth']
        person['place'] = row['place']
        person['number'] = row['number']


        # If already friends
        if row['status'] == 'confirmed':
            person['operation'] = 'Unfriend'

        # If unapprove friends
        if user_id == row['host_id'] and row['status'] == 'unconfirmed':
            person['operation'] = 'Cancel request'

        # If that person is the one who sent request
        if user_id == row['friend_id'] and row['status'] == 'unconfirmed':
            person['operation'] = 'Accept'

        people.append(person)
    return render_template("list.html", people=people)

