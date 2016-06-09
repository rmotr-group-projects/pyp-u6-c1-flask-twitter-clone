import sqlite3
from hashlib import md5         #hash function
from functools import wraps
from flask import Flask
from flask import (g, request, session, redirect, render_template,
                   flash, url_for)

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


# implement your views here
@app.route("/")
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['POST', 'GET'])
def login():
    error = None
    if request.method == 'GET':
        if 'username' in session:
            flash('You are already logged in')
            return redirect(url_for('own_feed')) #might need to pull username from db to pass to own_feed func
        return render_template('login.html')
    if request.method == 'POST':
        # request.form is dict with all the data from POST
        cur = g.db.execute('SELECT id, username, password FROM user WHERE username=?'\
        ,(request.form['username'],))
        user = cur.fetchone()
        if user:
            password_hash = md5(request.form['password'].encode('utf-8')).hexdigest()
            if password_hash != user[2]:
                flash('Invalid username or password')
                return redirect(url_for('login'))
            else:
                session['user_id'] = user[0]
                session['username'] = user[1]
                flash('Login successful')
                return redirect(url_for('own_feed', username = user[1]))
        else:
            flash('Invalid username or password')
            return redirect(url_for('login'))


@app.route('/logout/<username>') #add variable usernames
def logout(username):
    session.pop('username')
    flash('Logout successful')
    return redirect(url_for('login'))
    

@app.route('/profile', methods=['POST', 'GET'])


@app.route('/tweets/<username>', methods=['POST', 'GET'])
@login_required
def own_feed(username):
    
    pass
    

@app.route('/other_feed')
@login_required
def other_feed():
    render_template('other_feed.html')

@app.route('/tweets/<tweet-id>/delete', methods=['POST'])
@login_required
def delete_tweet():
    cur = g.db.execute('SELECT * from tweet where user_id=?', (session['user_id'],))
    if len(cur.fetchall()) < 2:
        flash("Sorry, you must have at least two tweets in order to delete one.")
        return redirect(url_for('own_feed'))
    
    cur = g.db.execute('DELETE FROM tweet WHERE id=?',(request.form['tweet-id'],))
    flash("Tweet deleted successfully.")
    return redirect(url_for('own_feed'))


