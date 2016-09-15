import sqlite3
from operator import itemgetter
from hashlib import md5
from functools import wraps
from flask import Flask
from flask import (g, request, session, redirect, render_template,
                   flash, url_for)

app = Flask(__name__)


def connect_db(db_name):
    return sqlite3.connect(db_name)


def validate(username, password):
    con = g.db
    validation = False
    with con:
        cur = con.cursor()
        cur.execute("SELECT * FROM user")
        rows = cur.fetchall()
        for row in rows:
            user = row[1]
            passw = row[2]
            if user == username:
                validation = check_password(passw, password)
    return validation


def check_password(hashed_password, user_password):
    return hashed_password == md5(user_password.encode()).hexdigest()


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


@app.route('/')
@login_required
def homepage():
    if session['username']:
        return own_feed(session['username'])
    else:
        redirect(url_for('login'))


@app.route('/login', methods = ['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        validation = validate(username, password)
        if validation == False:
            error = ' - Login Failed'
        else:
            session['username'] = username
            return redirect(url_for('own_feed', username = username))
    return render_template('/static_templates/login.html', error = error)


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/<username>', methods = ['GET', 'POST'])
@login_required
def own_feed(username):
    if session['username'] == username:
        if request.method == 'GET':
            sorted_tweets = sorted(_get_tweets_from_db(username), key=itemgetter('created'), reverse=True)
            return render_template('/static_templates/own_feed.html', tweets = sorted_tweets, username = username)
        if request.method == 'POST':
            g.db.execute('INSERT INTO tweet(user_id, content) VALUES((SELECT id FROM user WHERE username = "{0}"), "{1}");'.format(session['username'], request.form.get('content', type=str)))
            g.db.commit()
            sorted_tweets = sorted(_get_tweets_from_db(username), key=itemgetter('created'), reverse=True)
            return render_template('/static_templates/own_feed.html', tweets=sorted_tweets, username=username)
    else:
        sorted_tweets = sorted(_get_tweets_from_db(username), key=itemgetter('created'), reverse=True)
        return render_template('/static_templates/other_feed.html', tweets = sorted_tweets)


def _get_tweets_from_db(username):
    cursor = g.db.execute(
        'SELECT t.id, t.user_id, t.created, t.content, u.username FROM tweet t INNER JOIN user u ON t.user_id = u.id WHERE u.username = "{0}";'.format(
            session['username']))
    tweets = [dict(id=row[0], user_id=row[1], created=row[2], content=row[3], username=row[4]) for row in
              cursor.fetchall()]
    return tweets


@app.route('/tweets/<tweet_id>/delete', methods = ['POST'])
@login_required
def delete_tweet(tweet_id):
    g.db.execute('DELETE FROM tweet WHERE id = {}'.format(tweet_id))
    g.db.commit()
    return redirect(url_for('own_feed', username = session['username']))


@app.route('/profile', methods = ['GET'])
@login_required
def profile():
    if request.method == 'GET':
        cursor = g.db.execute('SELECT id, username, first_name, last_name, birth_date FROM user;')
        user = [dict(id = row[0], username = row[1], first_name = row[2], last_name = row[3], birth_date = row[4]) for row in cursor.fetchall()]
        return render_template('/static_templates/profile.html', user = user)
    if request.method == 'POST':
        return "Changes sub"
