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

sample1 = '04/19/2022'
sample2 = '2022-04-19'
sample3 = '2022'
sample4 = '2022-01'

sample5 = '2022-00'
sample6 = '2022-13'
sample7 = '2022-12-32'

sample8 = '2022/04/19'

def check_valid_datetime(date):
    year = ''
    month = ''
    day = ''

    n = len(date)
    print(f"len = {n}")
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
    
    print(year)
    print(month)
    print(day)

    if year.isnumeric() == False:
        print('year is not numeric')
        return False
    if len(month) > 0:
        if month.isnumeric() == True:
            if int(month) < 1 or int(month) > 12:
                return False
        else:
            print('month is not numeric')
            return False
    if len(day) > 0:
        if day.isnumeric() == True:
            if int(day) < 1 or int(day) > 31:
                return False
        else:
            print('day is not numeric')
            return False
    return True
            
print(check_valid_datetime(sample8))

