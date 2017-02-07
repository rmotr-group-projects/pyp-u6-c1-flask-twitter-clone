import sqlite3
from hashlib import md5
from functools import wraps
from flask import Flask
from flask import (g, request, session, redirect, render_template,
                       flash, url_for)

app = Flask(__name__)

# Logging
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# create a file handler
handler = logging.FileHandler('info.log')
handler.setLevel(logging.INFO)

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)

def connect_db(db_name):
    return sqlite3.connect(db_name)

@app.before_request
def before_request():
    g.db = connect_db(app.config['DATABASE'][1])


# DECORATORS

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login', next=request.url)), 302
        return f(*args, **kwargs)
    return decorated_function

# VIEWS

@app.route('/')
@login_required
def home():
    return redirect(url_for('user', user=session['username'])), 302

@app.route('/profile', methods=['GET','POST'])
@login_required
def profile():
    if request.method == 'POST':
        flash('Profile updated!')
        g.db.execute('\
            UPDATE user\
            SET first_name = ?, last_name = ?, birth_date = ?\
            WHERE id == ?',[
            request.form['first_name'],
            request.form['last_name'],
            request.form['birth_date'],
            session['user_id'],
            ])
        g.db.commit()
    
    user = g.db.execute('\
        SELECT username, first_name, last_name, birth_date\
        FROM user\
        WHERE id == ?',[
        session['user_id']
        ])
    user = user.fetchone()
    user = [ '' if n == None else n for n in user ]
    user = {
        'username': user[0],
        'first_name': user[1],
        'last_name': user[2],
        'birth_date': user[3],
        }
    return render_template('profile.html', user=user)


@app.route('/<user>', methods=['GET','POST'])
def user(user):
    
    # Someone tries to post tweet without being logged in
    if request.method == 'POST' and 'username' not in session:
        return '', 403
    
    # If viewing your own page
    if 'username' in session and session['username'] == user:
        
        if request.method == 'POST':
            print('request to post tweeT:', request.form['tweet'])
            g.db.execute('INSERT INTO "tweet" ("user_id", "content") VALUES (?, ?);',
            [
                session['user_id'],
                request.form['tweet'],
            ])
            g.db.commit()
            
            flash('Tweet posted!')
        
        tweets = get_tweets(user_id=session['user_id'])
        return render_template('home.html', tweets=tweets), 200
        
    else:
        user_id = username_to_id(user)
        tweets = get_tweets(user_id=user_id) 
        
    return render_template('user.html', tweets=tweets, username=user), 200

@app.route('/tweets/<int:id>')
def tweet(tweet):
    pass

@app.route('/tweets/<int:id>/delete', methods=['POST'])
@login_required
def tweet_delete(id):
    
    tweet = g.db.execute('\
        SELECT id FROM tweet \
        WHERE user_id == ? AND id == ?',
        [session['user_id'], id])
    tweet = tweet.fetchone()
    
    tweet = g.db.execute('\
        SELECT id FROM tweet \
        WHERE id == ?',
        [ id])
    tweet = tweet.fetchone()
    
    g.db.execute('DELETE FROM tweet WHERE id = ?', [id])
    g.db.commit()
    
    flash('Tweet deleted.')
    return redirect( url_for('home'), 302 )

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    
    flash('You have been logged out.')
    return redirect(url_for('home'), 302)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('home'), 302)
    
    if request.method == 'POST':
        user = g.db.execute('SELECT id, username, password FROM user WHERE username == ? AND password == ?', 
        [ 
        request.form['username'],
        md5(request.form['password'].encode('utf-8')).hexdigest()
        ])
        user = user.fetchone()
        if user:
            session['username'] = user[1]
            session['user_id'] = user[0]
            session.pop('_flashes', None)
            flash('Logged in successfully')
            return redirect(url_for('home'), 302)
        else:
            session.pop('_flashes', None)
            flash('Invalid username or password')

    return render_template('login.html')

# FUNCTIONS

def get_tweets(user_id):
    query = "SELECT id, created, content \
    FROM tweet \
    WHERE user_id == ?\
    ORDER BY created DESC"
    cursor = g.db.execute("SELECT id, created, content \
    FROM tweet \
    WHERE user_id == ?\
    ORDER BY created DESC", [user_id])
    tweets = [{ 'id':t[0], 'created':t[1], 'text':t[2] } for t in cursor.fetchall()]
    return tweets

def username_to_id(username):
    user = g.db.execute('SELECT id FROM user WHERE username == ?', [username])
    user = user.fetchone()
    return user[0]