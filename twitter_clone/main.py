import sqlite3
from hashlib import md5
from functools import wraps
from flask import Flask
from flask import (g, request, session, redirect, render_template,
                   flash, url_for, abort)

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
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    cursor_pw = g.db.execute('SELECT username, password FROM user;')
    cursor_id = g.db.execute('SELECT username, id FROM user;')
    users_pw = dict(cursor_pw.fetchall())
    users_id = dict(cursor_id.fetchall())

    if request.method == 'POST': # someone's trying to log in

        username = request.form['username']
        password = request.form['password']
        hashed_pw = md5(request.form['password'].encode('utf-8')).hexdigest()

        if username in users_pw:
            if users_pw[username] == hashed_pw:
                session['user_id'] =  users_id[username]
                session['username'] = username
                return redirect('/')
                # same as `return redirect(url_for('index'))` but now if we method name for route '/' it is okay

        else:
            error = "Invalid username or password"
    elif request.method == 'GET':
        if 'username' in session:
            return redirect('/')

    return render_template('login.html', error=error)

@app.route('/')
@login_required
def root():
    return redirect('/{}'.format(session['username']))

@app.route('/logout')
def logout():
    # second parameter means that nothing will happen if the key doesn't exist
    session.pop('user_id', None)
    session.pop('username', None)

    return redirect('/')


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    username = session['username']
    if request.method == 'GET':
        # get all the tweets
        pass
    elif request.method == 'POST':
        birth_date = request.form['birth_date']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        raw_sql = '''
            UPDATE user
            SET birth_date = '{}', first_name = '{}', last_name = '{}'
            WHERE username = '{}'
        '''.format(birth_date, first_name, last_name, session['username'])

        g.db.execute(raw_sql)
        g.db.commit()

    return render_template('profile.html', username = username)

# for passing parameters `<int:` makes sure the param is an integer
# @app.route('/page/<page_id>')
# def page(page_id):
#     pageid = page_id

@app.route('/tweets/<int:tweet_id>/delete', methods=['POST'])
@login_required
def delete(tweet_id):
    # import ipdb; ipdb.set_trace()

    if 2 > 1: # if authenticated (ie: the user owns the tweet)
        raw_sql = 'DELETE FROM tweet WHERE tweet.id = {}'.format(tweet_id)
        return redirect('/')
    else: # not authenticated
        return redirect(url_for('login'))

@app.route('/<username>', methods=['GET', 'POST'])
def view_feed(username):
    tweets = None
    get_user_sql = "SELECT * FROM user WHERE username='{}'".format(username)
    user = g.db.execute(get_user_sql).fetchone()
    user_id = user[0]

    if request.method == 'GET': # viewer wants to view a feed
        get_tweets_sql = '''
            SELECT *
            FROM tweet
            WHERE tweet.user_id = '{}'
        '''.format(user_id)

        tweets = g.db.execute(get_tweets_sql).fetchall()
        print tweets

        if 'username' in session: # viewer is logged in
            if session['username'] == username: # viewer is viewing their own feed
                return render_template('own_feed.html', session=session, tweets=tweets)
            else: # you are viewing someone else's feed
                return render_template('other_feed.html', session=session, tweets=tweets)
        else:
            return render_template('other_feed.html', session=session, tweets=tweets)
    elif request.method == 'POST':
        if 'username' in session and session['username'] == username:
            insert_tweet_sql = "INSERT INTO tweet ('user_id', 'content') VALUES ({}, '{}')".format(session['user_id'], request.form['tweet'])
            g.db.execute(insert_tweet_sql)
            g.db.commit()
            return render_template('own_feed.html', session=session, tweets=tweets)
        else:
            abort(403) # lol who knew you could just do this
