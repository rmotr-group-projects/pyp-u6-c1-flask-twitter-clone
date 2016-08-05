import sqlite3
from hashlib import md5
from functools import wraps
from flask import Flask
from flask import (g, request, session, redirect, render_template,
                   flash, url_for, abort, Response)
from hashlib import md5

app = Flask(__name__)


def connect_db(db_name):
    return sqlite3.connect(db_name)

def _hash_password(password):
    """
    Uses md5 hashing for now
    """
    hexd =  md5(password.encode("utf-8"))
    return hexd.hexdigest()


@app.before_request
def before_request():
    g.db = connect_db(app.config['DATABASE'][1])


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login', next=request.url)), 302
        return f(*args, **kwargs)
    return decorated_function


@app.route("/login", methods = ["GET", "POST"])
def login():
    """
    Log in page
    """
         
    if request.method == 'GET':
        #check if user is already logged in first, and if they are, redirect
        if 'logged_in' in session:
            response = Response(response = redirect(url_for('homepage', username = session['username'])) , status = 302)
            response.headers['location'] = "/"
            return response
        return render_template('login.html')
    
    elif request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        try:
            hashedPassword = _hash_password(password)
            query = "SELECT id, username FROM user WHERE username = ? AND password = ?"
            cursor = g.db.execute(query, (username, hashedPassword))
            results = cursor.fetchall()
            
            user_id = results[0][0]
            username = results[0][1]
            session["logged_in"] = True
            session["user_id"] = (user_id)
            session["username"] = username
            response = Response(response = redirect(url_for('display_feed', username = session['username'])), status = 200)
            return response
        except: # here
            return 'Invalid username or password', 200

@app.route("/<username>", methods = ["GET", "POST"])
def display_feed(username):
    #check if user is logged in as the page that they are visiting
    if 'username' in session:
        if session['username'] == username:
    
            if request.method == 'GET':
                tweets = _retrieve_tweets(session['user_id'])
                response = Response(response = render_template('own_feed.html', tweets=tweets), status = 200)
                return response
                
            if request.method == 'POST':
                _post_tweet(session['user_id'], request.form['tweet'])
                tweets = _retrieve_tweets(session['user_id'])
                response = Response(response = render_template('own_feed.html', tweets=tweets), status = 200)
                return response
                
        else:
            if request.method == 'GET':
                user_id = _get_user_id(username)
                tweets = _retrieve_tweets(user_id)
                return render_template('other_feed.html', tweets=tweets, username=username)
    #if user is not logged in 
    else: 
        if request.method == 'GET':
            user_id = _get_user_id(username)
            tweets = _retrieve_tweets(user_id)
            return render_template('other_feed.html', tweets=tweets, username=username)
            
        elif request.method == "POST":
            return redirect(url_for('login', next=request.url)), 403

@app.route("/tweets/<tweet_id>/delete", methods = ["POST"])
def delete(tweet_id):
    #if the user is not logged in, and tries to delete invalid tweet id
    if not _tweet_exists(tweet_id) and 'username' not in session:
        abort(404)
        
    #if the user is just not logged in
    if 'username' not in session:
        return redirect(url_for('login', next=request.url)), 302
        
    #if the user tries to delete invalid tweet
    if not _tweet_exists(tweet_id):
        abort(404)
        
    if _is_tweet_owner(tweet_id):
        _delete_tweet(tweet_id)
        response = Response(response = redirect(url_for('display_feed', username = session['username'])), status = 302)
        response.headers['location'] = "/"
        return response

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('homepage')), 302

@app.route("/profile", methods = ['GET', 'POST'])
@login_required
def profile():
    if request.method == 'GET':
        profile_details = _get_profile_information(session['user_id'])
        response = Response( response = render_template('profile.html', 
                                        first_name=profile_details[0][0], 
                                        last_name=profile_details[0][1], 
                                        birth_date=profile_details[0][2]), 
                                        status = 200 )
        return response
    if request.method == 'POST':
        username = request.form['username']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        birth_date = request.form['birth_date']
        _profile_update(first_name, last_name, birth_date)
        
        return render_template('profile.html', first_name=first_name, last_name=last_name, birth_date=birth_date)

@app.route('/')
def homepage():
    return redirect(url_for('login'))


def _is_tweet_owner(tweet_id):
    """
    Parameters: user = session["id], tweet id
    Return: boolean. True if user owns the tweet. False otherwise
    """
    query = "SELECT user_id FROM tweet WHERE id = ?"
    cursor = g.db.execute(query, (tweet_id,))
    results = cursor.fetchall()
    tweets_user_id = results[0][0]
    return int(tweets_user_id) == session["user_id"]

def _tweet_exists(tweet_id):
    query = "SELECT * FROM tweet WHERE id = ?"
    cursor = g.db.execute(query, (tweet_id,))
    results = cursor.fetchone()
    
    if results is None:
        return False
    return True

 
#SQL query helper functions
def _post_tweet(user_id, tweet_text):
    """
    Parameters: user_id and tweet contents
    Posts a tweet that belongs to user_id
    Checks if the 
    """
    #TODO: check if session user_id matches user_id to pass testcase
    query = 'INSERT INTO "tweet" ("user_id", "content") VALUES (?, ?)'
    g.db.execute(query, (user_id, tweet_text))
    g.db.commit()
    
def _delete_tweet(tweet_id):
    query = "DELETE FROM 'tweet' WHERE id = ?"
    g.db.execute(query, (tweet_id,))
    g.db.commit()
    
def _retrieve_tweets(user_id):
    query = "SELECT id, created, content FROM tweet WHERE user_id = ? ORDER BY created desc"
    cursor = g.db.execute(query, (user_id,))
    tweets = [dict(tweet_id = str(row[0]), created = row[1], content = row[2]) for row in cursor.fetchall()]
    return tweets

def _get_user_id(username):
    #Check if user exists
    query = "SELECT id FROM 'user' WHERE username = ?"
    cursor = g.db.execute(query, (username,))
    result = cursor.fetchall()
    user_id = str(result[0][0])
    return user_id

def _profile_update(first_name, last_name, birth_date):
    if len(birth_date) != 10:
        query = "UPDATE user SET first_name = ?, last_name = ? WHERE id = ?"
        g.db.execute(query, (first_name, last_name, session['user_id']))
    else:
        query = "UPDATE user SET first_name = ?, last_name = ?, birth_date = ? WHERE id = ?"
        g.db.execute(query, (first_name, last_name, birth_date, session['user_id']))
    g.db.commit()

def _get_profile_information(user_id):
    query = "SELECT first_name, last_name, birth_date FROM user WHERE id = ?"
    cursor = g.db.execute(query, (user_id,))
    results = cursor.fetchall()
    return results


if __name__ == "__main__":
    app.run()