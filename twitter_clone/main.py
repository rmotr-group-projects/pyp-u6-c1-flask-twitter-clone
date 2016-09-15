# -*- coding: utf-8 -*-
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
        return redirect(url_for('feed',username = session['username']))
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect('/') #not sure if this is correct implementation
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

        # Check validity of username and password, if valid, redirect to feed
        if username not in users:
            error = 'Invalid username or password' # Changed to pass test (JLZ) 
            # error = 'Invalid username'
        elif md5(request.form['password'].encode('utf-8')).hexdigest() != users[username][0]:
            error = 'Invalid username or password' # Changed to pass test (JLZ)
        else:
            session['logged_in'] = True
            session['username'] = username
            session['user_id'] = users[username][1]
            return redirect(url_for('feed', method='GET', username=username))
    return render_template('static_templates/login.html', error=error)


@app.route('/<username>', methods=['GET', 'POST'])
#@login_required
def feed(username):
    if request.method == 'POST':
        if 'username' not in session:
            return render_template('static_templates/login.html'), 403
        user_id = (g.db.execute('select id from user where username = ?',[username])).fetchone()[0]
        print(user_id)
        g.db.execute('INSERT INTO "tweet" ("user_id", "content") VALUES (?, ?);',(user_id,request.form['tweet']))    
        g.db.commit()

    cursor = g.db.execute("""
        SELECT a.id, a.username, c.id, c.content, c.created
        FROM user a INNER JOIN tweet c ON a.id = c.user_id
        WHERE a.username = ?
    """, [username])
    data = cursor.fetchall()
    print(data)
    if 'username' in session:
        if session['username'] == username:
            return render_template('static_templates/own_feed.html', username=username, data=data)
        else:
            return render_template('static_templates/other_feed.html', username=username,data=data)   
    else:
        return render_template('static_templates/other_feed.html', username=username, data=data)   

@app.route('/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect('/') #not sure if this is correct implementation

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    username = session['username']
    """
    if request.method == 'GET':
        cursor = g.db.execute('SELECT username, first_name, last_name, birth_date FROM user WHERE username = ?',[username])
        userdata = cursor.fetchall()
        return render_template('static_templates/profile.html',userdata=userdata)
    """
    if request.method == 'POST':
        g.db.execute('update user set first_name = ?, last_name = ?, birth_date = ? where username = ?',\
                         (request.form['first_name'],request.form['last_name'],request.form['birth_date'],username))
        g.db.commit()
    cursor = g.db.execute('SELECT username, first_name, last_name, birth_date FROM user WHERE username = ?',[username])
    userdata = cursor.fetchall()

    return render_template('static_templates/profile.html',userdata=userdata)

@app.route('/tweets/<int:tweet_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_tweet(tweet_id):
    cursor = g.db.execute("DELETE FROM tweet WHERE id = ?", (tweet_id, ))
    g.db.commit()
    return redirect('/')