from multiprocessing.dummy import Namespace
import os
from click import confirmation_option

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required


# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///mail.db")

sender_id = db.execute("SELECT user_id FROM informations WHERE email = ?", 'huyen@gmail.com')[0]['user_id']
receiver_id = db.execute("SELECT user_id FROM informations WHERE email = ?", 'nghia@gmail.com')[0]['user_id']
print(sender_id)
print(receiver_id)

rows = db.execute("SELECT * FROM mail_box WHERE sender_id = ? AND receiver_id = ?", sender_id , receiver_id)
print(rows)