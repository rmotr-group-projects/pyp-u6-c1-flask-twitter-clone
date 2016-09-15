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
    if request.method == 'POST':
        if request.form['username'] and request.form['password']:
            password = md5(request.form['password'].encode('utf-8')).hexdigest()
            sql_query = """
                Select * from 'user' where username = :username and password = :password;
            """
            result = g.db.execute(sql_query, {
                'username': request.form['username'],
                'password': password
            }).fetchone()
            if result and len(result) > 0:
                session['user_id'] = result[0]
                session['username'] = request.form['username']
            if not result:
                error = "Invalid username or password"
    if 'username' in session:
        if request.values.get('next'):
            return redirect(request.values.get('next'))
        return redirect(url_for('index'))
    
    return render_template('static_templates/login.html', error=error)


@app.route('/logout')
def logout():
    # remove the username from the session if it is there
    session.pop('username', None)
    session.pop('user_id', None)
    if request.values.get('next'):
        return redirect(request.values.get('next'))
    return redirect(url_for('index'))


@app.route('/')
@login_required
def index():
    return redirect(session['username'])


@app.route('/profile', methods=['GET','POST'])
@login_required
def profile_view():
    update_status = [None, None]
    def get_info():
        user_query = """Select username, first_name, last_name, birth_date from 'user' where id = :user_id;"""
        user_info = g.db.execute(user_query, {'user_id': session['user_id']}).fetchone()
        user_info = [i if i else "" for i in user_info]
        return render_template('static_templates/profile.html', user_info=user_info, update_status=update_status)
    
    def update_info():
        user_query = "UPDATE user SET first_name=?, last_name=?, birth_date=? WHERE id=?;"
        try:
            g.db.execute(user_query, 
                         (request.form['first_name'],
                          request.form['last_name'],
                          request.form['birth_date'],
                          session['user_id'])
                        )
            g.db.commit()
        except sqlite3.IntegrityError:
            update_status[0] = 'Error'
            update_status[1] = 'Invalid data entered'
            return get_info()
        update_status[0] = 'Success'
        update_status[1] = 'Your profile was correctly updated'
        return get_info()
    
    if (request.method == 'GET'):
        return get_info()
    
    if (request.method == 'POST'):
        return update_info()

    

@app.route('/<username>', methods=['GET','POST'])
def feeds(username):

    def read_feed():
        id_query = """Select id from 'user' where username = :username;"""
        user_id = g.db.execute(id_query, {'username': username}).fetchone()
        if not user_id:
            abort(404)
        tweet_query = """Select * from 'tweet' where user_id = :user_id;"""
        tweets = g.db.execute(tweet_query, {'user_id': user_id[0]}).fetchall()
        return render_template('static_templates/other_feed.html', tweets=tweets,
                                otheruser = username)
    
    def full_access_feed():
        sql_query = """Select * from 'tweet' where user_id = :user_id;"""
        tweets = g.db.execute(sql_query, {'user_id': session['user_id']}).fetchall()
        return render_template('static_templates/own_feed.html', tweets=tweets)
        #return render_template('static_templates/own_feed.html', tweets=tweets, session=session)
    
    def post_tweet():
        sql_query = """
                    INSERT INTO "tweet" ("user_id", "content") VALUES (?, ?);
                    """
        g.db.execute(sql_query, (
                        session['user_id'],
                        request.form['tweet']
                        ))
        g.db.commit()
    
    if 'username' not in session:
        if request.method == 'POST':
            abort(403)
        return read_feed()
    
    if username != session['username']:
        if request.method == 'POST':
            abort(403)
        return read_feed()
        
    if username == session['username']:
        if request.method == 'POST':
            post_tweet()
        return full_access_feed()
    

@app.route('/tweets/<int:tweet_id>/delete', methods=['POST'])
@login_required
def tweet_delete(tweet_id):
    sql_query = """
                DELETE FROM 'tweet' WHERE user_id=? and id=?;
            """
    g.db.execute(sql_query,(session['user_id'], tweet_id))
    g.db.commit()
    
    if request.values.get('next'):
        return redirect(request.values.get('next'))
    return redirect(url_for('index'))