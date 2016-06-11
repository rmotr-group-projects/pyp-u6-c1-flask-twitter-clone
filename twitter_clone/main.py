"""
/tweets/{{tweet['tweet_id']}}/delete?next=http://fornoodling-bdauer-1.c9users.io/{{tweet['name']}}
"""

import sqlite3
from hashlib import md5         #hash function
from functools import wraps
from flask import Flask
from flask import (g, request, session, redirect, render_template, flash, url_for)

app = Flask(__name__)


def connect_db(db_name):
    return sqlite3.connect(db_name)


@app.before_request
def before_request():
    '''
    Open a database connection before each request
    '''
    g.db = connect_db(app.config['DATABASE'][1])


@app.teardown_request
def teardown_request(exception):
    '''
    Close the database connection after each request if one exists
    '''
    db = getattr(g,'db',None)
    if db is not None:
        db.close()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


# implement your views here
@app.route('/')
def index():
    print "root webpage"
    return redirect(url_for('login'))


@app.route('/login')
def get_login():
    #print "in the get_login"
    #if 'username' in session:
        #flash('You are already logged in')
        #return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    # request.form is dict with all the data from POST
    cur = g.db.execute('SELECT id, username, password FROM user WHERE username=?'\
    ,(request.form['username'],))
    user = cur.fetchone()
    if user:
        password_hash = md5(request.form['password']).hexdigest()
        if password_hash != user[2]:
            flash('Invalid username or password')
            return redirect(url_for('login'))
        else:
            g.user_id = user[0]
            g.username = user[1]
            return redirect(url_for('own_feed', username = user[1]))
    else:
        flash('Invalid username or password')
        return render_template('login.html')


@app.route('/logout') #add variable usernames
@login_required
def logout():
    session.pop('username')
    session.pop('user_id')
    flash('Logout successful')
    return redirect(url_for('index'))
    

@app.route('/<username>', methods=['POST', 'GET'])
def tweets(username):
    prepared_statement = """
    select id, user_id, created, content from tweet where
    user_id='{}'
    """.format(username)
    cur = g.db.execute(prepared_statement)
    tweets = [dict(row(3)) for row in cur.fetchall()]
    
    if 'username' not in session:
        cur = g.db.execute('SELECT content FROM tweet INNER JOIN user ON'\
        'tweet.user_id = user.id')
        tweets = [dict(content=row[0]) for row in cur.fetchall()]
        return render_template('other_feed.html', username = username)
        
    return render_template('own_feed.html')


@app.route('/profile', methods=['POST', 'GET'])
@login_required
def profile():
    return render_template('profile.html', username = session['username'])




@app.route('/tweets/<username>', methods=['POST', 'GET'])
@login_required
def own_feed(username):
    
    prepared_statement = "SELECT id, user_id, created, content from tweet where user_id='{}'".format(get_user_id(username))
    cur = g.db.execute(prepared_statement)
    tweets = [dict(tweet_id=row[0], name=username, date=row[2], content=row[3]) for row in cur.fetchall()]
    return render_template("own_feed.html", tweets=tweets)

def get_user_id(username):
    """Get the userid of the username"""
    prepared_statement = """
    select id from user where username="{}"
    """.format(username)
    return g.db.execute(prepared_statement).fetchone()[0]
    

@app.route('/other_feed')
@login_required
def other_feed():
    render_template('other_feed.html')

@app.route('/tweets/<tweet_id>/delete', methods=['POST'])
@login_required
def delete_tweet(tweet_id):
    cur = g.db.execute('SELECT * from tweet where user_id=?', (session['user_id'],))
    if len(cur.fetchall()) < 2:
        flash("Sorry, you must have at least two tweets in order to delete one.")
        return redirect(url_for('own_feed'))
    
    cur = g.db.execute('DELETE FROM tweet WHERE id=?',(request.form['tweet-id'],))
    flash("Tweet deleted successfully.")
    return redirect(url_for('own_feed'))