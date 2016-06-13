"""
/tweets/{{tweet['tweet_id']}}/delete?next=http://fornoodling-bdauer-1.c9users.io/{{tweet['name']}}
"""


import sqlite3
from hashlib import md5         
from functools import wraps
from flask import Flask, json
from flask import g, request, session, redirect, render_template, flash, url_for


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


@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('tweets', username = session['username']))  #this is only a temporary fix; there must be a more eloquent implementation
    return redirect(url_for('get_login'))


@app.route('/login')
def get_login():
    if 'username' in session:
        flash('You are already logged in')
        return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    cur = g.db.execute('SELECT id, username, password, first_name, last_name, birth_date FROM user WHERE username=?'\
    ,(request.form['username'],))
    user = cur.fetchone()
    if user:
        pass_hash = md5(request.form['password']).hexdigest()
        if pass_hash != user[2]:
            flash('Invalid username or password')
            return redirect(url_for('login'))
        else:
            cols = ('user_id', 'username', 'password', 'first_name', 'last_name', 'birth_date')
            for k,v in zip(cols, user):
                session[k] = v
            return redirect(url_for('tweets', username = session['username']))
    else:
        flash('Invalid username or password')
        return render_template('login.html')


@app.route('/logout') #add variable usernames
@login_required
def logout():
    session.clear()
    flash('Logout successful')
    return redirect(url_for('index'))
    
    
# @app.route('/<username>')
# def get_tweets(username):
#     if session['username'] == username:
        

@app.route('/<username>', methods=['POST', 'GET'])
def tweets(username):
    if request.method == 'POST':
        tweet = request.form['tweet']
        insert_tweet(username, tweet)
    cur = g.db.execute('select id, created, content from tweet where user_id=? order by id desc', (get_user_id(username),))
    tweets = [dict(tweet_id = row[0], created = row[1], content = row[2]) for row in cur.fetchall()]
    if 'username' not in session or username != session['username']:
        return render_template('other_feed.html', tweets = tweets, username = username)
    return render_template('own_feed.html', tweets = tweets, username = username)


@app.route('/profile', methods=['POST', 'GET'])
@login_required
def profile():
    data = {
        'id':session['user_id'],
        'first_name':session['first_name'],
        'last_name':session['last_name'],
        'birth_date':session['birth_date']
    }
    return render_template('profile.html', data=data)


def get_first_name(username):
    """Get the firstname of the username"""
    prepared_statement = """
    select first_name from user where username='{}'
    """.format(username)
    return g.db.execute(prepared_statement).fetchone()[0]


def get_last_name(username):
    """Get the last name of the username"""
    prepared_statement = """
    select last_name from user where username='{}'
    """.format(username)
    return g.db.execute(prepared_statement).fetchone()[0]
    
    
def get_birth_date(username):
    """Get the birth_date of the username"""
    prepared_statement = """
    select birth_date from user where username='{}'
    """.format(username)
    return g.db.execute(prepared_statement).fetchone()[0]
    
    
def get_user_id(username):
    if username == 'favicon.ico':
        return None
    """Get the userid of the username"""
    prepared_statement = """
    select id from user where username="{}"
    """.format(username)
    return g.db.execute(prepared_statement).fetchone()[0]

def insert_tweet(username, tweet):
    """method to insert the tweet for the username"""
    user_id = get_user_id(username)
    prepared_statement = """
    insert into tweet (`user_id`, `content`) values ({}, '{}')
    """.format(user_id, tweet)
    g.db.execute(prepared_statement)
    g.db.commit()
   
   
@app.route('/tweets/<username>', methods=['POST', 'GET'])
@login_required
def own_feed(username):
    prepared_statement = "SELECT id, user_id, created, content from tweet where user_id='{}'".format(get_user_id(username))
    cur = g.db.execute(prepared_statement)
    tweets = [dict(tweet_id=row[0], name=username, date=row[2], content=row[3]) for row in cur.fetchall()]
    return render_template("own_feed.html", tweets=tweets)


@app.route('/other_feed')
@login_required
def other_feed():
    render_template('other_feed.html')


@app.route('/tweets/<int:tweet_id>/delete', methods=['POST'])
@login_required #not necessary
def delete_tweet(tweet_id):
    # cur = g.db.execute('SELECT * from tweet where user_id=?', (session['user_id'],))
    # if len(cur.fetchall()) < 2:
    #     flash("Sorry, you must have at least two tweets in order to delete one.")
    #     return redirect(url_for('own_feed')
    # cur = g.db.execute('DELETE FROM tweet WHERE id=?',(request.form['tweet-id'],))
    g.db.execute('DELETE FROM tweet WHERE id=?',(tweet_id,))
    g.db.commit()
    # cur = g.db.execute("SELECT id FROM tweet WHERE id=?",(tweet_id,))
    # tweet_id = cur.fetchone()
    flash("Tweet deleted successfully")
    # return str(tweet_id)
    return redirect(request.script_root)