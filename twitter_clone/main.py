import sqlite3
import sys
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


@app.route('/')
@login_required
def index():
    if 'username' in session:
        return redirect('/{}'.format(session['username']))

@app.route('/logout')
def logout_page():
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect('/')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'GET':
        if 'username' in session:
            return redirect('/')
        else:
            return render_template('login.html', code=200)
    elif request.method == 'POST':
        user_name = request.form['username']
        hash_pass = md5(request.form['password'].encode('utf-8')).hexdigest()

        query = 'SELECT id, password FROM user WHERE username=?;'
        cursor = g.db.execute(query, (user_name, ))
        user_match = cursor.fetchone()
        if user_match and user_match[1] == hash_pass:
            session['username'] = user_name
            session['user_id'] = user_match[0]
            return redirect('/{}'.format(user_name))
        else:
            return "Invalid username or password.", 200

@app.route('/<user_name>', methods=['GET', 'POST'])
def user_page(user_name):
    if request.method == 'GET':
        cursor = g.db.execute('SELECT tweet.id, tweet.created, tweet.content, user.username from tweet '
                              'INNER JOIN user ON tweet.user_id=user.id AND user.username=?;',(user_name, ))
        tweets = [dict(id=row[0], created=row[1], content=row[2], username=row[3]) for row in cursor.fetchall()]
        if 'username' in session:
            if session['username'] == user_name:
                return render_template('own_feed.html', code=200, user=user_name, tweets=tweets)
            return render_template('other_feed.html', code=200, user=session['username'], tweets=tweets)
        else:
            return render_template('other_feed.html', code=200, user='', tweets=tweets)
    elif request.method == 'POST':
        if 'username' in session:
            if session['username'] == user_name:
                new_tweet = request.form['tweet']
                cursor = g.db.execute('SELECT id FROM user WHERE username=?;', (user_name, ))
                user_id = cursor.fetchone()[0]
                g.db.execute('INSERT INTO tweet (user_id, content) VALUES (?, ?);', (user_id, new_tweet))
                g.db.commit()
                # I know the below code is repetitive. Could possibly do better with a redirect or something.
                cursor = g.db.execute('SELECT tweet.id, tweet.created, tweet.content, user.username from tweet '
                                      'INNER JOIN user ON tweet.user_id=user.id AND user.username=?;', (user_name,))
                tweets = [dict(id=row[0], created=row[1], content=row[2], username=row[3]) for row in cursor.fetchall()]
                return render_template('own_feed.html', code=200, user=user_name, tweets=tweets)
            return 'Not your username', 403
        else:
            return 'Not logged in', 403

@app.route('/profile', methods=['GET'])
def get_profile():
    if 'username' in session:
        user_name = session['username']
        cursor = g.db.execute('SELECT * FROM user WHERE username=?;', (user_name,))
        result = cursor.fetchone()
        user_id, username, password, first_name, last_name, birth_date = result
        return render_template('profile.html',
                               user=username, first_name=first_name,
                               last_name=last_name, birth_date=birth_date, code=200)
    else:
        return redirect(url_for('login'))

@app.route('/profile', methods=['POST'])
def post_profile():
    if 'username' in session:
        new_first_name = request.form['first_name']
        new_last_name = request.form['last_name']
        new_birth_date = request.form['birth_date']
        user_name = session['username']
        cursor = g.db.execute('SELECT id FROM user WHERE username=?;', (user_name,))
        user_id = cursor.fetchone()[0]
        g.db.execute('UPDATE user SET first_name=?, last_name=?, birth_date=? WHERE id=?',
                     (new_first_name, new_last_name, new_birth_date, user_id))
        g.db.commit()
        return '', 200

@app.route('/tweets/<tweet_num>/delete', methods=['POST'])
def delete_tweet(tweet_num):
    cursor = g.db.execute('SELECT user_id FROM tweet WHERE id=?;', (tweet_num,))
    result = cursor.fetchone()
    if result is None:
        return 'Invalid tweet number', 404
    if 'username' not in session:
        return redirect(url_for('login'))
    else:
        # tweet is valid, get the user_id and username to check that person has authorization
        user_id = result[0]
        cursor = g.db.execute('SELECT username FROM user WHERE id=?;', (user_id,))
        user_name = cursor.fetchone()[0]
        if user_name != session['username']:
            return 'User is not authorized', 404
        else:
            g.db.execute('DELETE FROM tweet WHERE id=?;', (tweet_num,))
            g.db.commit()
            return redirect('/')
