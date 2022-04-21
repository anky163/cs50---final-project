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



def convert_datetime(date):

    day = ''
    month = ''
    year = ''

    slash = 0
    for c in date:
        if c == '/':
            slash += 1
        if c != '/' and slash == 0:
            month += c
        if c != '/' and slash == 1:
            day += c
        if c != '/' and slash == 2:
            year += c
    date = year + '-' + month + '-' + day 

    day = ''
    month = ''
    year = ''

    dash = 0
    for c in date:
        if c == '-':
            dash += 1
        if c != '-' and dash == 1:
            year += c
        if c != '-' and dash == 2:
            month += c
        if c != '-' and dash == 3: 
            day += c 
    date = year + '-' + month + '-' + day

    return(date)


