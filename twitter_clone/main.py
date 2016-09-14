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
def hello_world():
    return "Welcome to Twitter Clone"

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        
        # Pull query to grab usernames and password from db
        cursor = g.db.execute("""
            SELECT username, password
            FROM user;
            """)
        
        # Put usernames and passwords into dictionary
        users = {}
        for row in cursor.fetchall():
            users[row[0]] = row[1]
        username = request.form['username']
        
        # Check validity of username and password, if valid, redirect to feed
        if username not in users:
            error = 'Invalid username'
        elif request.form['password'] != users[username]:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            return redirect(url_for('own_feed', method='GET', username=username))
    return render_template('static_templates/login.html', error=error)

# # @app.route('/own_feed/<username>')
# def show_user_profile(username):
#     # show the user profile for that user
#     return 'User %s' % username
@app.route('/<username>', methods=['GET', 'POST'])
def own_feed (username):
    if request.method == 'GET':
        
        cursor = g.db.execute("""
            SELECT a.id as user_id, a.username as username, c.id as tweet_id, c.content as tweet_content, c.created as tweet_time
            FROM user a INNER JOIN tweet c ON a.id = c.user_id;
        """)
        data = cursor.fetchall()
        
        # It would be more efficient to use WHERE in the SQL query in order to
        # only pull tweets that match username. For sake of time, we move on.
        tweets = []
        for row in data:
            if row[1] == username:
                tweets.append(row)

        return render_template('static_templates/own_feed.html', username=username, data=tweets)

        