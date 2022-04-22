import os
import requests
import urllib.parse

from cs50 import SQL
from flask import redirect, request, session, render_template
from functools import wraps


# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///mail.db")


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function



def check_valid_datetime(date):
    year = ''
    month = ''
    day = ''

    n = len(date)

    if n < 4 or n > 10:
        return False

    for i in range(n):
        if i < 4:
            year += date[i]
        elif i > 4 and i < 7:
            month += date[i]
        elif i > 7 and i < 10:
            day += date[i]
        if i == 4 and date[i] != '-':
            return False
        if i == 7 and date[i] != '-':
            return False

    if year.isnumeric() == False:
        return False
    if len(month) > 0:
        if month.isnumeric() == True:
            if int(month) < 1 or int(month) > 12:
                return False
        else:
            return False
    if len(day) > 0:
        if day.isnumeric() == True:
            if int(day) < 1 or int(day) > 31:
                return False
        else:
            return False
    return True


def information_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get("user_id")

        rows = db.execute("SELECT * FROM informations WHERE user_id = ?", user_id)
        if len(rows) == 0:
            message = 'You must provide you informations first!'
            return render_template("information.html", requirement=message) 

        return f(*args, **kwargs)
    return decorated_function

