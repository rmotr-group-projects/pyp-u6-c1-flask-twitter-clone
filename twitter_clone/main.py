import sqlite3
from hashlib import md5
from functools import wraps
from flask import Flask
from flask import (g, request, session, redirect, render_template,
                   flash, url_for)
import os


app = Flask(__name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:################################session
            return redirect(url_for('login', next=request.url), code=302)
        return f(*args, **kwargs)
    return decorated_function


# implement your views here
@app.route('/')
@login_required
def homepage():
    return render_template('own_feed.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    error = None
    if request.method == 'POST':
        x = valid_login(request.form['username'], "{}".format(md5(request.form['password']).hexdigest()))
        if x:
            #log_the_user_in(request.form['username'])
            session['username'] = request.form['username']
            session['user_id'] = x
            return redirect(url_for('homepage'), code=302)
        else:
            error = 'Invalid username or password'
            flash(error, category='message')
    if request.method == 'GET' and session:
        return redirect(url_for('homepage'))
    # the code below is executed if the request method  was GET or the credentials were invalid
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop("username", None)
    session.pop('user_id', None)
    return redirect(url_for('homepage'))


def connect_db(db_name):
    return sqlite3.connect(db_name)


@app.before_request
def before_request():
    g.db = connect_db(app.config['DATABASE'][1])

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


def valid_login(par, param):
    #curs = g.db.cursor()
    users_cursor = g.db.execute('SELECT * FROM user')
    users_data = users_cursor.fetchall()
    for x in users_data:
        if par in x and param in x:
            print("ayto einai to id:" + str(x[0]))
            return x[0]
    return False
