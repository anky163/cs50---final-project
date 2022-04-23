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



# Provide input for sending.html
@app.route("/send", methods=["POST"])
@login_required
@information_required
def sent():
    name = request.form.get("name")
    email = request.form.get("email")
    return render_template("sending.html", name=name, email=email)


# SENDING MAIL
@app.route("/sending", methods=["GET", "POST"])
@login_required
@information_required
def sending():
    user_id = session['user_id']
    # Query all the mails that users sent
    rows = db.execute("SELECT * FROM mail_box WHERE sender_id = ? ORDER BY date DESC", user_id)
    mails = []
    for row in rows:
        mail = {}
        mail['receiver'] = row['receiver']
        receiver_id = row['receiver_id']
        receiver_email = db.execute("SELECT email FROM informations WHERE user_id = ?", receiver_id)[0]['email']
        mail['email'] = receiver_email
        mail['date'] = row['date']
        mail['mail'] = row['mail']

        mails.append(mail)
    head = 'Send mail'
    if request.method == "GET":
        return render_template("sending.html", mails=mails, head=head)
    
    name = request.form.get("receiver")
    email = request.form.get("email")
    mail = request.form.get("mail")

    receiver_id = db.execute("SELECT user_id FROM informations WHERE name = ? AND email = ?", name, email)
    if len(receiver_id) == 0:
        head = 'Friend not found!'
        return render_template("sending.html", mails=mails, head=head)
    receiver_id = receiver_id[0]['user_id']

    # Check whether receiver is in friendlist or not
    rows = db.execute("SELECT * FROM friends WHERE host_id = ? AND friend_id = ? AND status = ? OR host_id = ? AND friend_id = ? AND status = ?", user_id, receiver_id, 'confirmed', receiver_id, user_id, 'confirmed')
    if len(rows) == 0:
        head = 'Friend not found!'
        return render_template("sending.html", mails=mails, head=head)

    # Update mail_box
    sender = db.execute("SELECT name FROM informations WHERE user_id = ?", user_id)[0]['name']
    sender_id = user_id
    receiver = name
    receiver_id = db.execute("SELECT user_id FROM informations WHERE email = ?", email)[0]['user_id']
    date = datetime.datetime.now()
    db.execute("INSERT INTO mail_box (sender, sender_id, receiver, receiver_id, date, mail) VALUES (?, ?, ?, ?, ?, ?)", sender, sender_id, receiver, receiver_id, date, mail)

    return redirect("/sending")



# SEARCH SENT MAILS IN sending.html
@app.route("/search_sent", methods=["GET", "POST"])
@login_required
def search_sent():
    if request.method == "POST":
        user_id = session['user_id']
        rows = []

        name = request.form.get('name')
        if not name:
            message = "Name required!"
            return render_template("sending.html", name_required=message)
        name = '%' + name + '%'

        receiver_email = request.form.get('receiver_email')
        if receiver_email:
            receiver_email = '%' + receiver_email + '%'

        date = request.form.get('date')
        if date:
            if check_valid_datetime(date) == False:
                message = 'Invalid date'
                return render_template("sending.html", date=message)
            date = '%' + date + '%'

        if not receiver_email and not date:
            rows = db.execute("SELECT * FROM mail_box WHERE sender_id = ? AND receiver LIKE ?", user_id, name)
        elif receiver_email and not date:
            rows = db.execute("SELECT * FROM mail_box WHERE sender_id = ? AND receiver LIKE ? AND receiver_id IN (SELECT user_id FROM informations WHERE email LIKE ?)", user_id, name, receiver_email)
        else:
            rows = db.execute("SELECT * FROM mail_box WHERE sender_id = ? AND receiver LIKE ? AND receiver_id IN (SELECT user_id FROM informations WHERE email LIKE ?) AND date LIKE ?", user_id, name, receiver_email, date)

        if len(rows) == 0:
            message = 'Not found!'
            return render_template("sending.html", notfound=message)

              
        mails = []
        for row in rows:
            mail = {}
            mail['receiver'] = row['receiver']
            receiver_id = row['receiver_id']
            mail['email'] = db.execute("SELECT email FROM informations WHERE user_id = ?", receiver_id)[0]['email']
            mail['mail'] = row['mail']
            mail['date'] = row['date']
            mails.append(mail)
        return render_template("sending.html", mails=mails)
    return redirect("/sending")


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
        name = '%' + name + '%'

        sender_email = request.form.get('sender_email')
        if sender_email: 
            sender_email = '%' + sender_email + '%'

        date = request.form.get('date')

        if date:
            if check_valid_datetime(date) == False:
                message = 'Invalid date'
                return render_template("inbox.html", date=message)
            date = '%' + date + '%'

        if not sender_email and not date:
            rows = db.execute("SELECT * FROM mail_box WHERE receiver_id = ? AND sender LIKE ?", user_id, name)
        elif sender_email and not date:
            rows = db.execute("SELECT * FROM mail_box WHERE receiver_id = ? AND sender LIKE ? AND sender_id IN (SELECT user_id FROM informations WHERE email LIKE ?)", user_id, name, sender_email)
        else:
            rows = db.execute("SELECT * FROM mail_box WHERE receiver_id = ? AND sender LIKE ? AND sender_id IN (SELECT user_id FROM informations WHERE email LIKE ?) AND date LIKE ?", user_id, name, sender_email, date)
            
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
    user_id = session['user_id']
    if request.method == "GET":
       
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
        rows = db.execute("SELECT * FROM informations JOIN friends ON user_id = host_id OR user_id = friend_id WHERE host_id = ? OR friend_id = ? ORDER BY friends.id DESC", user_id, user_id)

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
                    person['button'] = 'Send mail'

                # If unapproved friends
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
        rows = db.execute("SELECT * FROM informations JOIN friends ON user_id = host_id OR user_id = friend_id WHERE host_id = ? AND friend_id IN (SELECT user_id FROM informations WHERE name LIKE ?) OR host_id IN (SELECT user_id FROM informations WHERE name LIKE ?) AND friend_id = ? ORDER BY name, status", user_id, name, name, user_id)

    if email:
        rows = db.execute("SELECT * FROM informations JOIN friends ON user_id = host_id OR user_id = friend_id WHERE host_id = ? AND friend_id IN (SELECT user_id FROM informations WHERE name LIKE ? AND email LIKE ?) OR host_id IN (SELECT user_id FROM informations WHERE name LIKE ? AND email LIKE ?) AND friend_id = ? ORDER BY name, status", user_id, name, email, name, email, user_id)

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
                person['button'] = 'Send mail'

            # If unapprove friends
            if user_id == row['host_id'] and row['status'] == 'unconfirmed':
                person['operation'] = 'Cancel request'

            # If that person is the one who sent request
            if user_id == row['friend_id'] and row['status'] == 'unconfirmed':
                person['operation'] = 'Accept'

            people.append(person)
    return render_template("list.html", people=people)



# FRIEND REQUESTSS
@app.route("/requests", methods=["GET", "POST"])
@login_required
@information_required
def requests():
    user_id = session['user_id']
    if request.method == "GET":
        # Select all people that sent requests to user BUT user has not accepted yet
        rows = db.execute("SELECT * FROM informations JOIN friends ON user_id = host_id WHERE friend_id = ? AND status = ? ORDER BY status, name DESC", user_id, 'unconfirmed')
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