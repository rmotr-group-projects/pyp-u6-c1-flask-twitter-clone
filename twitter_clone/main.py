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

# login view
@app.route('/login', methods=['GET', 'POST'])
def login():
    next = request.args.get('next', '/')
    if 'username' in session:
        return redirect(next)

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = g.db.execute("SELECT * from user WHERE username=:username;",
                              {'username': username})
        user_from_db = cursor.fetchone()
        hashed_passwd = md5(password.encode('utf-8')).hexdigest()

        if user_from_db and (hashed_passwd == user_from_db[2]):
            session["username"] = username
            session["user_id"] = user_from_db[0]
            flash("You are correctly logged in")

            return redirect("/", 302)
        else:
            flash("Invalid username or password", 'danger')

    return render_template("login.html", next=next)


@app.route('/')
@login_required
def home():
    return render_template('dyn_own_feed.html')


@app.route('/logout')
@login_required
def logout():
    next = request.args.get('next', '/')
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(next)


@app.route('/<username>', methods=['GET', 'POST'])
def twitter_feed(username):
    if request.method == 'POST':
        if 'username' not in session:
            # user not logged in
            return redirect('/', 403)

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
        return redirect('/', 404)

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

    if session.get('username', None) == username:
        return render_template('dyn_own_feed.html', tweets=tweets)
    return render_template('dyn_other_feed.html', tweets=tweets)


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'GET':
        cursor = g.db.execute(
            "SELECT username, first_name, last_name, birth_date from user WHERE username=:username",
            {'username': session['username']})
        username, first_name, last_name, birth_date = cursor.fetchone()

        return render_template('dyn_profile.html', username=username,
                               first_name=first_name, last_name=last_name,
                               birth_date=birth_date)

    elif request.method == 'POST':
        params = {
            'first_name': request.form['first_name'],
            'last_name': request.form['last_name'],
            'birth_date': request.form['birth_date'],
            'username': session['username']
        }
        # print("USERNAME TYPE")
        # print(type(params['username']))
        # update database with new values
        try:
            cursor = g.db.execute(
                "UPDATE user SET first_name=:first_name, last_name=:last_name, birth_date=:birth_date WHERE username=:username;",
                params)
            g.db.commit()
        except sqlite3.IntegrityError:
            print("follow the rules yo!")

        post_cursor = g.db.execute(
            "SELECT username, first_name, last_name, birth_date from user WHERE username=:username;",
            {'username': session['username']})
        username, first_name, last_name, birth_date = post_cursor.fetchone()

        return render_template('dyn_profile.html', username=username,
                               first_name=first_name, last_name=last_name,
                               birth_date=birth_date)


@app.route('/tweets/<int:msg_id>/delete', methods=['POST'])
@login_required
def tweet(msg_id):
    next = request.args.get('next', '/')
    # check if tweet exists
    cursor = g.db.execute(
        "SELECT user_id FROM tweet WHERE id=:msg_id;",
        {'msg_id': msg_id})
        
    tweet = cursor.fetchone()
    print (tweet)
    if tweet:
        g.db.execute("DELETE FROM tweet WHERE id=:msg_id",
                     {'msg_id': msg_id})
        g.db.commit()
        return redirect(next, 302)
    else:
        abort(404)


        # remove tweet
        # return to profile page
