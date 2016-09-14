import sqlite3
from hashlib import md5
from functools import wraps
from flask import Flask
from flask import (g, request, session, redirect, render_template,
                   flash, url_for)

app = Flask(__name__)


def connect_db(db_name):
    return sqlite3.connect(db_name)


def validate(username, password):
    con = g.db
    validation = False
    with con:
        cur = con.cursor()
        cur.execute("SELECT * FROM user")
        rows = cur.fetchall()
        for row in rows:
            user = row[1]
            passw = row[2]
            if user == username:
                validation = check_password(passw, password)
    return validation


def check_password(hashed_password, user_password):
    return hashed_password == md5(user_password.encode()).hexdigest()


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


@app.route('/')
@login_required
def homepage():
    return redirect(url_for('own_feed'))



@app.route('/login', methods = ['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        validation = validate(username, password)
        if validation == False:
            error = ' - Login Failed'
        else:
            session['username'] = username
            return redirect(url_for('own_feed'))
    return render_template('/static_templates/login.html', error = error)


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/own_feed', methods = ['GET', 'POST'])
@login_required
def own_feed():
    cursor = g.db.execute('SELECT t.id, t.user_id, t.created, t.content, u.username FROM tweet t INNER JOIN user u ON t.user_id = u.id WHERE u.username = "{0}";'.format(session['username']))
    tweets = [dict(id = row[0], user_id = row[1], created = row[2], content = row[3]) for row in cursor.fetchall()]
    return render_template('/static_templates/own_feed.html', tweets = tweets)


@app.route('/profile', methods = ['GET'])
@login_required
def profile():
    if request.method == 'GET':
        cursor = g.db.execute('SELECT id, username, first_name, last_name, birth_date FROM user;')
        user = [dict(id = row[0], username = row[1], first_name = row[2], last_name = row[3], birth_date = row[4]) for row in cursor.fetchall()]
        return render_template('/static_templates/profile.html', user = user)
    if request.method == 'POST':
        return "Changes sub"
