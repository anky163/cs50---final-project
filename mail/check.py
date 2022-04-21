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

date = '04/19/2022'

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
date = '-' + year + '-' + month + '-' + day + '-'

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
print(date)
