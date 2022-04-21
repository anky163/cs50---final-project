import os
import requests
import urllib.parse

from flask import redirect, request, session
from functools import wraps



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


