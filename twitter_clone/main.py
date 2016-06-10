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
    
def query_db(query, args=(), one=False):
    cur = g.db.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv
    
def auth_login(usr_name, password):
    usr = g.db.execute('select username, password from user where username = ?', [usr_name]).fetchone()
    if usr is None:
        return False
    else:
        return md5(password).hexdigest() == usr[1]

# implement your views here
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if not auth_login(request.form['username'], request.form['password']):
            error = 'Invalid username or password'
            return render_template('login.html', error=error)
        else:
            session['username'] = request.form['username']
            session['user_id'] =  g.db.execute('select id from user where username = ?', [request.form['username']]).fetchone()[0]
            return redirect(url_for('index'))
    
    if request.method == 'GET':
        if 'username' in session:
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error=error)
    
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/')
@login_required
def index():
    return render_template('static_templates/own_feed.html/')

@app.route('/<username>', methods=['GET', 'POST'])
def user_feed(username):
    if session:
        own_feed = username == session['username']
    else:
        own_feed = False
    
    if request.method == 'GET':
        if own_feed:
            tweets = query_db('select * from tweet where user_id = ?', [session['user_id']])
            return render_template('feed.html', username=username, own_feed=own_feed, tweets=tweets)
        else:
            usr_id = g.db.execute('select id from user where username = ?', [username]).fetchone()[0]
            tweets = query_db('select * from tweet where user_id = ?', [usr_id]) 
            return render_template('feed.html', username=username, own_feed=own_feed, tweets=tweets)
        
    if request.method == 'POST':
        if own_feed:
            pass # be able to post new tweets or delete tweets
        else: #other users
            return redirect(url_for('index'), code=403)
#     # return other_feed.html

# Needs GET and POST support

#build dynamic templates

# if not a session
# you can just see the tweets
# should query db for username and post all tests in descending order creation date

# if it's your page( and logged in/session)
# form to post new tweets
# button to delete linked tweets

# if method is post
#   add the new tweet to the db
#   reload the page render page w/ new db pull with new tweet
# 
#     pass

@app.route('/profile', methods = ['GET','POST'])
@login_required
def user_profile():
# check if user logged in
# updates all info for profile, then sends to db
    if request.method == 'POST':
        try:
            new_user = request.form['username']
            new_first = request.form['first_name']
            new_last = request.form['last_name']
            new_bday = request.form['birth_date']
            # can probably reformat and make less than 80 the next line
            g.db.execute('UPDATE user SET username = ?, first_name = ?, last_name = ?, birth_date = ? WHERE id = ?',
            [new_user, new_first, new_last, new_bday, session['user_id']])
            g.db.commit()
            flash('Profile updated correctly.')
        except:
            flash('Profile not updated.')
            
# return profile.html
# need dynamic html page to return new information
# has html form containg all current info from db:
#   user, first, last, birthdate
# render the page with new info  # TODO make new dynamic page 
#     pass

# @app.route('/tweets/<int:id (tweet table)>/delete')
# def delete_tweet():
    # pass