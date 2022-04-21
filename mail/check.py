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

dates = '2002/12/08 11-25-31'
date = '2002/12/08'
date = '%' + date + '%'
print(date)