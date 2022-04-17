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

friend_name = 'ds nghia'
birth = ''
place = ''
number = ''
email = ''
name = db.execute("SELECT * FROM informations WHERE name = ?", friend_name)
print(name)