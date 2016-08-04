import sqlite3
from hashlib import md5
from functools import wraps
from flask import Flask
from flask import (g, request, session, redirect, render_template,
                   flash, url_for, abort)
import re
from auxiliary import (hash_function, get_user_tweets, string_transform,
                        basic_query, basic_insert, transform_update_string, basic_update)


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


# Index view ###################################################################
@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('feed', username=session['username']))
    return redirect(url_for('login'))


# Login view ###################################################################
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    users = basic_query('user', 'username, password, id')
    
    if request.method == 'POST':
        username = request.form['username']
        password = hash_function(request.form['password'])
        
        for user in users:
            if user[0] == username and user[1] == password:
                session['username'] = username
                session['user_id'] = user[2]
                flash('You were logged in')
                return redirect(url_for('index'))
        error = 'Invalid username or password'
    if request.method == "GET":
        # Might need extra checks to be extra prudent with logging in/sessions
        if 'username' in session:
            return redirect(url_for('index'))
    return render_template('login.html', error=error)
    
    
# Profile view #################################################################
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    succesful_profile_update = None
    if request.method == 'POST':
        form = request.form
        
        '''Hard coded update'''
        query = 'UPDATE user SET first_name = "{}", last_name = "{}", birth_date = \
        "{}" WHERE username = "{}"'.format(form['first_name'], form['last_name'], \
        form['birth_date'], session['username'])
        
        g.db.execute(query)
        g.db.commit()
        
        succesful_profile_update = "Your profile was correctly updated"
        
    user_data = {}
    users = basic_query('user', 'username, first_name, last_name, birth_date')
    for user in users:
        if session['username'] == user[0]:
            user_data = {'username':user[0], 'first_name':user[1], 'last_name':user[2], 'birth_date':user[3]}
             
    return render_template('profile.html', user=user_data, success = succesful_profile_update)


# Tweets view ##################################################################
@app.route('/tweets/<int:tweet_id>/delete', methods=['GET', 'POST'])
@login_required
def tweets(tweet_id):
    user_tweets = get_user_tweets(session['user_id'])
    deletion_query = 'DELETE FROM tweet WHERE id = ?;'
    for tweet in user_tweets:
        if tweet['tweet_id'] == tweet_id:
            g.db.execute(deletion_query, [tweet_id])
            g.db.commit()
    return redirect(url_for('index'))
            

# Feed view ####################################################################
@app.route('/<username>', methods=['GET', 'POST'])
def feed(username):
    
    ### Gets user Tweets ###
    user_id = None
    # Returns a list of tuples with (unicode) username and user_id
    users = basic_query('user', 'username, id')
    # Loop through the list of tuples and check to see if the <username> is in it
    for user in users:
        if username == user[0]:
            # if username is in it, let's assign that usernames id to the local user_id variable
            user_id = user[1]
    
    user_tweets = get_user_tweets(user_id)

    ### User Tweeting ###
    if request.method == 'POST':
        
        # There's probably a more elegant way of doing this..
        try:
            if username != session['username']:
                abort(403)
        except:
            abort(403)
            
        tweet_text = str(request.form['tweet'])
        
        basic_insert('tweet', '(user_id, content)', (user_id,tweet_text))
        
        user_tweets = get_user_tweets(user_id)
        return render_template('own_feed.html', username=session['username'], tweets=user_tweets)
        
    if 'username' in session and session['username'] == username:
        return render_template('own_feed.html', username=session['username'], tweets=user_tweets)
    elif 'username' in session:
        return render_template('other_feed.html', username=session['username'], tweet_user=username, tweets=user_tweets)
    else:
        return render_template('other_feed.html', username=None, tweet_user=username, tweets=user_tweets)

        
# Logout view ##################################################################
@app.route('/logout')
def logout(next=None):
    session.pop('username', None)
    session.pop('user_id', None)
    if next:
        return redirect(next)
    return redirect(url_for('index'))