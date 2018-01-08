import sqlite3
from hashlib import md5
from functools import wraps
from flask import Flask
from flask import (g, request, session, redirect, render_template,
                   flash, url_for)
                   
"""
This program is a website similar to what you would find at twitter.com. It uses 
the flask microframework. A user can log in, look at their profile, update their
profile information, and write tweets.

Demo username: martinzugnoni
Demo password: 1234
"""

app = Flask(__name__)


def connect_db(db_name):
    return sqlite3.connect(db_name)


@app.before_request
def before_request():
    g.db = connect_db(app.config['DATABASE'][1])


def login_required(f):
    """
    This decorator forces the user to log in before visiting certain parts of 
    the website.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            # User is not logged in
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
@login_required
def index():
    if 'username' in session:
        # User is already logged in
        return redirect('/{}'.format(session['username']))
        

@app.route('/login', methods=['POST', 'GET'])
def login():
    """
    The user must log in using a valid username and password in order to see and 
    write tweets.
    """
    
    # Flask processes request data, and gives access to it though the request 
    # global object. 
    next_ = request.args.get('next', '/')

    if 'username' in session:
        # User is already logged in
        return redirect(next_)
    
    if request.method == 'POST':
        #  Extract user info, and get a hash of the password
        username = request.form['username']
        password = request.form['password']
        
        # WARNING: MD5 is a vulnerable hash function and it's not recommended for production
        password_md5 = md5(password.encode('utf-8')).hexdigest()
        
        # Get the password and other info for the user from the database
        query = 'SELECT id, password FROM user WHERE username=:username;'
        cursor = g.db.execute(query, {'username': username})
        user = cursor.fetchone() # (user_id, password_md5)
        
        # If user is none, then that user is not in the databse.
        # Also, check that the user entered a valid password.
        if user and user[1] == password_md5:
            session['username'] = username
            session['user_id'] = user[0]
            return redirect(next_)
            
        return "Invalid username or password"

    return render_template('static_templates/login.html')


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    """Log the user out."""
    if 'username' in session:
        # User is already logged in
        next_ = request.args.get('next', '/')
        session.pop('username')
        session.pop('user_id')
        return redirect(next_)
        

@app.route('/profile', methods=['POST', 'GET'])
@login_required
def profile():
    """Shows the user's profile. The user can update their information here."""
    if request.method == 'POST':
        # Update the user's info with what has been sent to the forms
        query = """UPDATE user 
                  SET first_name=:first_name, last_name=:last_name, birth_date=:birth_date 
                  WHERE username=:username;"""
        query_args = {
            'first_name': request.form.get('first_name'),
            'last_name': request.form.get('last_name'),
            'birth_date': request.form.get('birth_date'),
            'username': session['username']
        }
        g.db.execute(query, query_args)
        g.db.commit()
    
    # Get the user's current information so it can be displayed on the form
    username = session['username']
    query = 'SELECT first_name, last_name, birth_date FROM user WHERE username=:username;'
    cursor = g.db.execute(query, {'username': username})
    first_name, last_name, birth_date = cursor.fetchone()
    
    return render_template('static_templates/profile.html', username=username, 
              first_name=first_name, last_name=last_name, birth_date=birth_date)


# No login is required for looking at a user's feed
@app.route('/<username>', methods=['POST', 'GET'])
def feed(username):
    """Show the users feed."""
    if request.method == 'POST':
        if 'username' not in session:
            return render_template('403.html'), 403
            
        tweet = request.form.get('tweet')
        
        if not tweet:
            return 'Please type something for your tweet'
        else:
            # Send the tweet that was written in the form
            query = 'INSERT INTO tweet ("user_id", "content") VALUES (:user_id, :content);'
            query_args = {'user_id': session['user_id'], 'content': tweet}
            cursor = g.db.execute(query, query_args)
            g.db.commit()
    
    cursor = g.db.execute("SELECT id FROM user WHERE username=:username;", 
                                                         {'username': username})
    user = cursor.fetchone()
    
    if not user:
        # User is not in the database
        return render_template('404.html'), 404
    
    #  Get user info for the template
    query = """SELECT t.id, t.created, t.content
              FROM user AS u
              JOIN tweet t ON (u.id=t.user_id)
              WHERE u.username=:username
              ORDER BY datetime(t.created) DESC;"""
    cursor = g.db.execute(query, {'username': username})
    
    tweets = [dict(username=username, id=row[0], created=row[1], 
                                  content=row[2]) for row in cursor.fetchall()]
        
    return render_template('feed.html', feed_username=username, tweets=tweets)


@app.route('/tweets/<int:tweet_id>/delete', methods=['POST'])
@login_required
def tweet(tweet_id):
    """Deletes a tweet."""
    next_ = request.args.get('next', '/')
    
    # Get the tweet's info
    select_query = 'SELECT * FROM tweet WHERE id=:tweet_id AND user_id=:user_id;'
    select_query_args = {'tweet_id': tweet_id, 'user_id': session['user_id']}
    cursor = g.db.execute(select_query, select_query_args)

    # Error if the user has no info in the database
    if not cursor.fetchone():
        return render_template('404.html'), 404
    
    # Delete the tweet
    delete_query = 'DELETE FROM tweet WHERE id=:tweet_id AND user_id=:user_id;'
    delete_query_args = {'tweet_id': tweet_id, 'user_id': session['user_id']}
    g.db.execute(delete_query, delete_query_args)
    g.db.commit()
    
    return redirect(next_)