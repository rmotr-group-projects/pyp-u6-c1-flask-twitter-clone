import sqlite3
from hashlib import md5
from functools import wraps
from flask import Flask
from flask import (g, request, session, redirect, render_template,
                   flash, url_for)

app = Flask(__name__)


def connect_db(db_name):
    return sqlite3.connect(db_name)


@app.before_request
def before_request():
    g.db = connect_db(app.config['DATABASE'][1])


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    if request.method == 'POST':
        # check if username in database, not get all users
        # request.form is dict with all the data from POST
        # request.form[user], request.form[password]

        cur = g.db.cursor()
        cur.execute\
        ('SELECT username, password FROM user' +
        'WHERE username={0}, password={1}'.\
        format(request.form['username'], request.form['password']))
        user = cur.fetchone()
        '''
        cursor = g.db.execute + \
        ('SELECT username, password FROM user' +
        'WHERE username={0}, password={1}'. \
        format(request.form['username'], request.form['password']))
        user = cursor.fetchone()
        '''
        if user:
            return url_for('profile.html', user=user)


# implement your views here
@app.route("/")
def main():
    return render_template('profile.html')