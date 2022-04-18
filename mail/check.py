import os
from click import confirmation_option

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required


# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///mail.db")

row = db.execute("SELECT name, email FROM informations WHERE name = ? AND email = ?", 'ds nghia', 'nghia@gmail.com')

names = []
value = {}
value['name'] = row[0]['name']
value['email'] = row[0]['email']
names = [value]

print(names)
for val in names:
    print(val)

