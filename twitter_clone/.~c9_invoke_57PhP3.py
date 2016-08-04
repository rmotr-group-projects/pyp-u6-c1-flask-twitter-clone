import sqlite3
from hashlib import md5
from functools import wraps
from flask import Flask
from flask import (g, request, session, redirect, render_template,
                   flash, url_for)

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('home')), 302
    cur = g.db.cursor()
    if request.method == 'POST':
        user = request.form['username']
        pw = md5(request.form['password'].encode('utf-8')).hexdigest()
        cur.execute('SELECT * from user WHERE username = ? AND password = ?',
        (user, pw))

        fetched = cur.fetchone()
        if fetched is None:
            return "Invalid username or password", 200

        session['logged_in'] = True
        session['user_id'] = fetched[0]
        session['username'] = fetched[1]
        session['fname'] = fetched[3]
        session['lname'] = fetched[4]
        session['bdate'] = fetched[5]
        return redirect(url_for('feed',username=session['username']))

    return render_template('static_templates/login.html')


@app.route('/<username>', methods=['GET'])
def feed(username):
    flash('flashy message')
    if 'username' not in session or session['username'] != username:
        return other_feed(username)
    else:
        return own_feed(username)

def own_feed(username):
    user_id = session['user_id']
    cur = g.db.cursor()
    cur.execute('SELECT id, content, created from tweet WHERE user_id = ?',
    (user_id,))
    my_tweets = cur.fetchall()
    return render_template('static_templates/own_feed.html',
    username=username,tweets=my_tweets)


def other_feed(username):
    if 'username' in session:
        me = session['username']
    else:
        me = ''
    cur = g.db.cursor()
    cur.execute('SELECT id, username from user WHERE username = ?',
    (username,))
    fetched = cur.fetchone()
    user_id = fetched[0]
    user = fetched[1]

    cur.execute('SELECT id,content,created from tweet WHERE user_id = ?',
    (user_id,))

    tweets = cur.fetchall()
    return render_template('static_templates/other_feed.html',
    me=me,username=user,tweets=tweets), 200


@app.route('/<username>', methods=['POST'])
@login_required
def post_tweet(username):
    cur = g.db.cursor()
    tweet = request.form['tweet']
    user_id = session['user_id']
    cur.execute('INSERT INTO tweet ("user_id","content") VALUES (?, ?)',
    (user_id, tweet))
    if cur.rowcount != 1:
        return redirect(url_for('home'), 
    g.db.commit()
    cur.execute('SELECT id, content, created from tweet WHERE user_id = ?',
    (user_id,))
    my_tweets = cur.fetchall()
    return r


@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('feed',username=session['username']))
    else:
        return redirect(url_for('login'))


@app.route('/tweets/<int:tweet_id>/delete', methods=['POST'])
@login_required
def delete_tweet(tweet_id):
    cur = g.db.cursor()
    if 'user_id' in session:
        user_id = session['user_id']
        cur.execute('DELETE FROM tweet WHERE id = ? AND user_id = ?',
        (tweet_id,user_id))
    if cur.rowcount != 1:
        return redirect(url_for('home')), 403
    g.db.commit()
    flash('Tweet deleted.')
    return redirect(url_for('home'))


@app.route('/logout')
@login_required
def logout():
    session['logged_in'] = False
    session.pop('username', None)
    session.pop('user_id', None)
    flash('Logged out.')
    return redirect(url_for('home'))


@app.route('/profile', methods = ['GET'])
@login_required
def profile():
    return render_template('static_templates/profile.html',
    username = session['username'], birth_date = session['bdate'],
    first_name = session['fname'], last_name = session['lname']), 200


@app.route('/profile', methods=['POST'])
@login_required
def edit_profile():
    cur = g.db.cursor()

    username = request.form['username']
    fname = request.form['first_name']
    lname = request.form['last_name']
    bdate = request.form['birth_date']

    session['fname'] = fname
    session['lname'] = lname
    session['bdate'] = bdate

    cur.execute('UPDATE user SET "first_name" = ?, "last_name" = ?, "birth_date" = ? WHERE "username" = ?',
    (fname,lname,bdate,username))
    g.db.commit()
    return render_template('static_templates/profile.html',
    username = session['username'], birth_date = session['bdate'],
    first_name = session['fname'], last_name = session['lname']), 200