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
    #return "Welcome to Twitter Clone"
    if 'username' in session:
        return redirect(url_for('own_feed',username = session['username']))
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect('http://localhost/') #not sure if this is correct implementation
    error = None
    if request.method == 'POST':
        
        # Pull query to grab usernames and password from db
        cursor = g.db.execute("""
            SELECT username,  password, id
            FROM user;
            """)
        
        # Put usernames and passwords into dictionary of tuples
        users = {}
        for row in cursor.fetchall():
            # print(row)
            users[row[0]] = (row[1], row[2])
        username = request.form['username']
        # For clarity but may result in errors if username not in users
        # password = users[username][0]
        # user_id = users[username][1]
        
        # print("username = {}".format(username))
        # print("password = {}".format(password))
        # print("user_id = {}".format(user_id))

        # Check validity of username and password, if valid, redirect to feed
        if username not in users:
            error = 'Invalid username or password' # Changed to pass test (JLZ) 
            # error = 'Invalid username'
        elif md5(request.form['password']).hexdigest() != users[username][0]:
            error = 'Invalid username or password' # Changed to pass test (JLZ)
        else:
            session['logged_in'] = True
            session['username'] = username
            session['user_id'] = users[username][1]
            return redirect(url_for('own_feed', method='GET', username=username))
    return render_template('static_templates/login.html', error=error)


@app.route('/<username>', methods=['GET', 'POST'])
@login_required
def own_feed(username):
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

@app.route('/logout')
@login_required
def logout():
    # session.pop('logged_in', None)
    # flash('You were logged out')
    #session['logged_in'] = False
    #session['user_id'] = None
    #session['username'] = None
    session.pop('logged_in', None)
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect('http://localhost/') #not sure if this is correct implementation


@app.route('/tweets/<tweet_id>/delete')
@login_required
def delete_tweet(tweet_id, username):
    sql_statement = "DELETE FROM tweet WHERE id={}".format(tweet_id)
    cursor = g.database.execute(sql_statement)
    return redirect(url_for('own_feed', username=username))
    