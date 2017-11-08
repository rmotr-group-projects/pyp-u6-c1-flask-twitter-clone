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
@app.route('/')
@login_required
def index():
    return ""

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'GET':
        if 'username' in session:
            return redirect('/')
        else:
            return render_template('static_templates/login.html')
    elif request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        params = {
            'username': username,
            'password': md5(password.encode('utf-8')).hexdigest()
        }
        cursor = g.db.execute('SELECT * FROM user WHERE username = :username AND password = :password;', params)
        user = cursor.fetchone()
        if user:
            session['username'] = username
            session['user_id'] = user[0]
        else:
            return "Invalid username or password", 200
        return redirect('/')
        
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect('/')
        