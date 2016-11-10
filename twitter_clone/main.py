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
    next = request.args.get('next', '/')

    if 'username' in session:
        # already logged in
        return redirect(next)

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor = g.db.execute(
            'SELECT id, password FROM user WHERE username=:username;',
            {'username': username})
        user = cursor.fetchone()
        hashed_passwd = md5(password.encode('utf-8')).hexdigest()
        if user and user[1] == hashed_passwd:
            session['user_id'] = user[0]
            session['username'] = username
            flash('You were correctly logged in', 'success')
            return redirect(next)

        # authentication faild
        flash('Invalid username or password', 'danger')

    return render_template('login.html', next=next)


@app.route('/logout')
@login_required
def logout():
    next = request.args.get('next', '/')
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You were correctly logged out', 'info')
    return redirect(next)


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        query = """
            UPDATE user
            SET first_name=:first_name, last_name=:last_name, birth_date=:birth_date
            WHERE username=:username;
        """
        params = {
            'first_name': request.form.get('first_name'),
            'last_name': request.form.get('last_name'),
            'birth_date': request.form.get('birth_date'),
            'username': session['username']
        }
        try:
            g.db.execute(query, params)
            g.db.commit()
        except sqlite3.IntegrityError:
            flash('Something went wrong while updating your profile', 'danger')
        else:
            flash('Your profile was correctly updated', 'success')

    cursor = g.db.execute(
        'SELECT username, first_name, last_name, birth_date FROM user WHERE username=:username;',
        {'username': session['username']})
    username, first_name, last_name, birth_date = cursor.fetchone()
    return render_template('profile.html', username=username, first_name=first_name,
                           last_name=last_name, birth_date=birth_date)


@app.route('/<username>', methods=['GET', 'POST'])
def feed(username):
    if request.method == 'POST':
        if 'username' not in session:
            # user not logged in
            return render_template('403.html'), 403

        tweet = request.form.get('tweet')
        if not tweet:
            flash('Please write something in your tweet', 'danger')
        else:
            query = 'INSERT INTO tweet ("user_id", "content") VALUES (:user_id, :content);'
            params = {'user_id': session['user_id'], 'content': tweet}
            try:
                g.db.execute(query, params)
                g.db.commit()
            except sqlite3.IntegrityError:
                flash('Something went wrong while saving your tweet', 'danger')
            else:
                flash('Thanks for your tweet!', 'success')

    # check if given username exists
    cursor = g.db.execute(
        'SELECT id FROM user WHERE username=:username;', {'username': username})
    user = cursor.fetchone()
    if not user:
        return render_template('404.html'), 404

    # fetch all tweets from given username
    cursor = g.db.execute(
        """
        SELECT u.username, u.first_name, u.last_name, t.id, t.created, t.content
        FROM user AS u JOIN tweet t ON (u.id=t.user_id)
        WHERE u.username=:username ORDER BY datetime(created) DESC;
        """,
        {'username': username})
    tweets = [dict(username=row[0], id=row[3], created=row[4], content=row[5])
              for row in cursor.fetchall()]
    return render_template('feed.html', feed_username=username, tweets=tweets)


@app.route('/tweets/<int:tweet_id>/delete', methods=['POST'])
@login_required
def tweet(tweet_id):
    next = request.args.get('next', '/')
    cursor = g.db.execute(
        'SELECT * FROM tweet WHERE id=:tweet_id AND user_id=:user_id;',
        {'tweet_id': tweet_id, 'user_id': session['user_id']})
    if not cursor.fetchone():
        return render_template('404.html'), 404
    g.db.execute(
        'DELETE FROM tweet WHERE id=:tweet_id AND user_id=:user_id',
        {'tweet_id': tweet_id, 'user_id': session['user_id']})
    g.db.commit()
    flash('Your tweet was successfully deleted!', 'success')
    return redirect(next)


@app.route('/', methods=['GET'])
@login_required
def index():
    if 'username' in session:
        return redirect('/{}'.format(session['username']))
