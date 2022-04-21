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

row = db.execute("SELECT * FROM friends WHERE host_id = ? AND friend_id = ?", 20, 21)
print(len(row))