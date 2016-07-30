import sqlite3
from hashlib import md5
from functools import wraps
from flask import Flask
import random
from flask import (g, request, session, redirect, render_template,
                   flash, url_for, abort)

app = Flask(__name__)


def connect_db(db_name):
    #make connection to database before each request
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


@app.route('/login', methods=['GET','POST'])
def login():
    if 'username' in session:
        return redirect(url_for('index'))
        
    if request.method == 'GET':
        return render_template('login.html')
        
    elif request.method == 'POST':
        query = "SELECT * FROM user WHERE username=:username AND password=:password"
        val = g.db.execute(query, {
            'username' : request.form['username'],
            'password' : md5(request.form['password']).hexdigest()})
            
        row = val.fetchone()
        if row != None:
            session["user_id"] = row[0]
            session["username"] = request.form['username']
            flash('You have been logged in')
            return redirect(url_for('index'))
            
        return render_template('login.html', error = 'Invalid username or password')

    


@app.route('/profile', methods = ['GET', 'POST'])
@login_required
def profile():
    username = session['username']
    user_id = session['user_id']
    
    #return form
    if request.method == 'GET':
        return render_template('profile.html', username = session["username"])
        
    #submit form
    if request.method == 'POST':
        data = (request.form['first_name'], request.form['last_name'], request.form['birth_date'], user_id )
        g.db.execute("UPDATE user SET first_name=?, last_name=?, birth_date =? WHERE user.id=?", data)
        g.db.commit()
        flash("Profile Updated")
    
    val = g.db.execute('SELECT first_name, last_name, birth_date FROM user where id= (?)', (user_id,))
    
    first_name, last_name, birth_date = tuple(val.fetchall()[0])
    return render_template('profile.html', first_name = first_name, last_name = last_name, \
                            birth_date = birth_date, value = username)
    

@app.route('/<username>', methods = ['GET', 'POST'])
def feed(username):
    
    #user logged in, but not their feed
    
    #user not logged in, but can see other peoples tweets, DONE
    if 'username' not in session:
        if request.method == 'POST':
            return abort(403)
        elif request.method == 'GET':
            cursor = g.db.execute("SELECT content, created FROM tweet, user WHERE username = ? AND user_id = user.id", (username,))
            tweets = [dict(username=username, tweet=row[0], date=row[1]) for row in cursor.fetchall()]
            return render_template('other_feed.html', tweets = tweets)
    else:
        #user logged in, their feed, DONE
        if session['username'] == username:
            if request.method == 'GET':
                cursor = g.db.execute("SELECT tweet.id, content, created FROM tweet, user WHERE username = ? AND user_id = user.id", (username,))
                tweets = [dict(username=username, tweet_id=row[0], tweet=row[1], date=row[2]) for row in cursor.fetchall()]
                return render_template('own_feed.html', tweets = tweets)
            elif request.method == 'POST':
               return render_template('own_feed.html', tweets = tweet(username)) 
        #logged in but viewing other feed
        else:
            cursor = g.db.execute("SELECT content, created FROM tweet, user WHERE username = ? AND user_id = user.id", (username,))
            tweets = [dict(username=username, tweet=row[0], date=row[1]) for row in cursor.fetchall()]
            return render_template('other_feed.html', tweets = tweets)
            

#Helper function to tweet
def tweet(username):
    user_id = session['user_id']
    tweet_content = request.form['tweet']
    
    if len(tweet_content) < 140:
        g.db.execute('INSERT INTO tweet(user_id, content) VALUES(:user_id, :content)', {"user_id":user_id, "content":tweet_content})
        g.db.commit()
        flash("Tweet sent")
        
        cursor = g.db.execute("SELECT tweet.id, content, created FROM tweet, user WHERE username = ? AND user_id = user.id", (username,))
        tweets = [dict(username=username, tweet_id=row[0], tweet=row[1], date=row[2]) for row in cursor.fetchall()]
        return tweets
    

@app.route('/tweets/<tweet_id>/delete', methods = ['POST'])
def delete_tweet(tweet_id):
    #tweet_id = tweets[1]
    if not str(tweet_id).isdigit():
        return abort(404)
    
    if 'username' not in session:
        return redirect(url_for('login'))
    else:
        g.db.execute('DELETE FROM tweet WHERE id=:id', {"id" : tweet_id})
        g.db.commit()
        flash('Tweet deleted')
    
    return redirect(url_for('index'))


@app.route('/')
@login_required
def index():
    #If user is not logged in, redirect to /login
    #if user is logged in, redirect to /username
    return redirect(url_for('profile'))


@app.route('/logout', methods = ['GET'])
@login_required
def logout():
    session.clear()
    flash('Logout successful')
    return redirect(url_for('index'))