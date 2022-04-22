from multiprocessing.dummy import Namespace
import os
from click import confirmation_option

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from sqlalchemy import null
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required



# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///mail.db")

user_id = 33
name = '%k%'
string = f"SELECT user_id FROM informations WHERE name LIKE ?"
print(string)


rows = db.execute("SELECT * FROM informations JOIN friends ON user_id = host_id OR user_id = friend_id WHERE host_id = ? AND friend_id IN (SELECT user_id FROM informations WHERE name LIKE ?) OR host_id IN (SELECT user_id FROM informations WHERE name LIKE ?) AND friend_id = ?", user_id, name, name, user_id)
print(rows)