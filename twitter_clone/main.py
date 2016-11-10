import sqlite3
from sqlite3 import IntegrityError
from hashlib import md5
from functools import wraps
from flask import Flask
from flask import (abort, g, request, session, redirect, render_template,
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


# implement your views here
def query_db(query, args=(), one=False):
    cur = g.db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv


@app.route('/<username>', methods=['POST', 'GET'])
def feed(username):
    if request.method == 'POST':
        if not session.get('user_id', None):
            abort(403)
            return redirect('/', 403)

        query_db('insert into tweet (content, user_id) values (?, ?)',
                 [request.form['tweet'], session.get('user_id')])

        g.db.commit()

        flash('New entry was successfully posted')

    if username == session.get('username'):
        tweets = query_db('''
                SELECT t.*, u.username FROM tweet t
                INNER JOIN user u ON t.user_id = u.id WHERE EXISTS
                  (SELECT * FROM following f WHERE f.user_id = ?) ORDER BY t.created DESC''',
                          [session.get('user_id')])

        return render_template('static_templates/own_feed.html', tweets=tweets)

    else:
        print(username)
        tweets = query_db('''
            SELECT t.*, u.username FROM tweet t INNER JOIN user u
                   ON t.user_id = u.id
                   WHERE username=? ORDER BY t.created DESC''', [username])

        return render_template('static_templates/other_feed.html', tweets=tweets)


@app.route('/')
@login_required
def home():
    users = query_db('''
            SELECT * FROM user
            WHERE id != ? ORDER BY username''', [session.get('user_id')])
    return render_template('static_templates/home.html', users=users)
    # return redirect(url_for('feed', username=session.get('username')))


@app.route('/follow/<int:id>', methods=['POST'])
@login_required
def follow(id):
    try:
        query_db('INSERT INTO following(user_id, follower_id) VALUES(?, ?)', [session.get('user_id'), id])
        g.db.commit()
    except IntegrityError:
        flash('You are already following this user.')
    return redirect('/')


@app.route('/tweets/<int:id>/delete', methods=['POST'])
@login_required
def delete_tweet(id):
    query_db('DELETE FROM tweet WHERE id=?', [id])
    g.db.commit()
    return redirect('/')


@app.route('/profile', methods=['POST', 'GET'])
@login_required
def profile():
    if request.method == 'POST':
        # query db for users == user
        username = request.form['username']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        birth_date = request.form['birth_date']

        query_db('''UPDATE user
                SET username = ?, first_name= ?, last_name = ?, birth_date = ?
                WHERE id = ?''',
                 [username, first_name, last_name, birth_date, session.get('user_id')])

        g.db.commit()

    user = query_db('SELECT * FROM user WHERE id = ?',
                    [session.get('user_id')], one=True)

    return render_template('static_templates/profile.html', user=user)


@app.route('/login', methods=['POST', 'GET'])
def login():
    if session.get('username'):
        return redirect('/')

    if request.method == 'POST':
        # query db for users == user
        username = request.form['username']
        password = md5(request.form['password'].encode('utf-8')).hexdigest()

        user = query_db('SELECT * FROM user WHERE username = ? and password = ?',
                        [username, password], one=True)

        if not user:
            error = 'Invalid username or password'
            return render_template('static_templates/login.html', error=error)
        else:
            session['username'] = username
            session['user_id'] = user['id']
            flash('You were logged in')
            return redirect('/')

    return render_template('static_templates/login.html')


@app.route('/logout')
def logout():
    if session.get('username', None):
        session.pop('username')
    if session.get('user_id', None):
        session.pop('user_id')

    return redirect('/')
