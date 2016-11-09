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


# implement your views here
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    cursor = g.db.execute('SELECT username, password FROM user;')
    if request.method == 'POST': # someone's trying to log in
        username = request.form['username']
        password = request.form['password']
        hashed_pw = md5(request.form['password'].encode('utf-8')).hexdigest()
        
        if valid_credentials(username, hashed_pw):
            session['user_id'] = 1 # hardcode for now it should be the user ID from the db
            session['username'] = username
            
            return redirect(url_for('index'))
        else:
            error = "Invalid username or password"

    return render_template('login.html', error=error)
    
@app.route('/')
@login_required
def index():
    return redirect(url_for('login'))
    
@app.route('/logout')
def logout():
    # second parameter means that nothing will happen if the key doesn't exist
    session.pop('user_id', None)
    session.pop('username', None) 

    return redirect(url_for('index'))
    
def valid_credentials(username, hashed_pw):
    if username == 'testuser1' : # hardcoded for now. implement sql checking
        # should return the user's ID somehow for session
        return True
    else:
        return False