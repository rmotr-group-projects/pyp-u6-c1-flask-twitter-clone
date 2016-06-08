import sqlite3
from hashlib import md5
from functools import wraps
from flask import Flask
from flask import (g, request, session, redirect, render_template,
                   flash, url_for)
import datetime

app = Flask(__name__)

DANGER = 'danger'
SUCCESS = 'success'

def connect_db(db_name):
    return sqlite3.connect(db_name)


def _hash_password(password):
    '''
    Returns the MD5 hash of the user's entered password
    '''
    password_bytes = str.encode(password)
    return md5(password_bytes).hexdigest()


def _date_check(date):
    '''
    Check for date format accuracy
    '''
    try:
        return datetime.datetime.strptime(date, '%Y-%m-%d')
    except:
        return False


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
def base():
    '''
    Redirect user to login page.
    '''
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    else:
        return redirect(url_for('feed'))
        


@app.route('/login', methods=['GET', 'POST'])
def login():
    '''
    Present user to login page redirect to feed if already logged in
    '''
    
    if request.method == 'GET':
        return render_template('login.html')
        
    else:
        error = None
        
        # Set cursor for db user table and pull all id, usernames, and password
        cursor = g.db.execute('SELECT id, username, password from user;')
        results = cursor.fetchall()
        ids = [entry[0] for entry in results]
        users = [entry[1] for entry in results]
        pws = [entry[2] for entry in results]

        user_pass = _hash_password(request.form['password'])
        user_name = request.form['username']
        
        # For each user in cursor, check if username and password are appropriate
        if user_name not in users:
            flash('Invalid username')
            flash_type = DANGER
        elif user_pass not in pws:
            flash('Invalid password')
            flash_type = DANGER
        else:
            session['logged_in'] = True
            session['username'] = user_name
            session['id'] = ids[users.index(user_name)]
            flash('You were logged in')
            flash_type = SUCCESS
            return redirect(url_for('feed', username=user_name))
        return render_template('login.html', flash_type=flash_type)


@app.route('/logout')
def logout():
    '''
    Log out the user and redirect to the login page.
    Alternatively, could redirect to the frontpage (user feed)
    '''
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('id', None)
    flash('You were logged out')
    return redirect(url_for('login'))
    
    
@app.route('/<username>', methods=['GET', 'POST'])
def feed(username):
    # return '<h1>Here we are: Feed!</h1>'
    # Display the user's twitter feed page.
    
    # Get all tweet data for this user.
    # Note: may need to sort this.
    query = '''SELECT u.username, t.id, t.created, t.content 
        FROM user as u INNER JOIN tweet as t
        WHERE u.username=? AND u.id=t.user_id;'''
    cursor = g.db.execute(query, (username,))
    tweets = cursor.fetchall()
    
    # Is the user logged in and viewing their own page?
    own = ('logged_in' in session and username == session['username'])
    
    if request.method == 'POST':
        if tweet in request.form:
            # Add tweet to db
            pass
        else:
            # Redirect to delete
            pass
    
    return render_template('feed.html', own=own, tweets=tweets)


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    '''
    Obtain the user details and pass to the profile templage for reply.
    '''
    error = None 
    flash_type = SUCCESS
    # return render_template('login.html')
    query = '''SELECT username, first_name, last_name, birth_date 
        FROM user
        WHERE id=?;'''
    cursor = g.db.execute(query, (str(session['id']),))
    results = cursor.fetchone()
    (user, fn, ln, dob) = results

    if request.method == 'POST':

        # If the user supplies an invalid date, error out and don't save
        if request.form['birth_date'] and not _date_check(request.form['birth_date']):
            flash('Invalid date')
            flash_type = DANGER
            
        # If the user supplies no date or a valid date, save the updates
        else:
            query = '''UPDATE user 
                SET first_name=?, last_name=?, birth_date=? 
                WHERE id=?;'''
            fn = request.form['first_name'] or fn
            ln = request.form['last_name'] or ln
            dob = request.form['birth_date'] or dob
            cursor = g.db.execute(query, (fn, ln, dob, str(session['id'])))
            
            flash('Updated')

    return render_template('profile.html', user=user, fname=fn, lname=ln, dob=dob, flash_type=flash_type)
