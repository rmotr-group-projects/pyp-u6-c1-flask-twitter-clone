"""
/tweets/{{tweet['tweet_id']}}/delete?next=http://fornoodling-bdauer-1.c9users.io/{{tweet['name']}}
"""


import sqlite3
from hashlib import md5         
from functools import wraps
from flask import Flask, json
from flask import g, request, session, redirect, render_template, flash, url_for


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


@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('tweets', username = session['username']))  
    return redirect(url_for('get_login'))


@app.route('/login')
def get_login():
    if 'username' in session:
        flash('You are already logged in')
        return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    cur = g.db.execute('SELECT id, username, password, first_name, last_name, birth_date FROM user WHERE username=?'\
    ,(request.form['username'],))
    user = cur.fetchone()
    if user:
        pass_hash = md5(request.form['password']).hexdigest()
        if pass_hash != user[2]:
            flash('Invalid username or password')
            return redirect(url_for('login'))
        else:
            cols = ('user_id', 'username', 'password', 'first_name', 'last_name', 'birth_date')
            for k,v in zip(cols, user):
                session[k] = v
            return redirect(url_for('tweets', username = session['username']))
    else:
        flash('Invalid username or password')
        return render_template('login.html')


@app.route('/logout') #add variable usernames
@login_required
def logout():
    session.clear()
    flash('Logout successful')
    return redirect(url_for('index'))
    
        
@app.route('/<username>', methods=['POST', 'GET'])
def tweets(username):
    if request.method == 'POST':
        if 'username' not in session:
            return redirect(url_for('index'), code = 403)
        g.db.execute('INSERT INTO tweet (user_id, content) VALUES (?,?)',(session['user_id'],request.form['tweet']))
        g.db.commit()
    cur = g.db.execute('SELECT id, created, content FROM tweet WHERE user_id=? ORDER BY created DESC', (get_user_id(username),))    #should implement join statement
    tweets = [dict(tweet_id = row[0], created = row[1], content = row[2]) for row in cur.fetchall()]
    if request.method == 'GET':
        if 'username' not in session or username != session['username']:
            return render_template('other_feed.html', tweets = tweets, username = username)
    return render_template('own_feed.html', tweets = tweets, username = username)


@app.route('/profile', methods=['POST', 'GET'])
@login_required
def profile():
    if request.method == 'POST':
        g.db.execute('UPDATE user SET username=?, first_name=?, last_name=?, birth_date=? WHERE id=?', (request.form['username'], request.form['first_name'], request.form['last_name'], request.form['birth_date'], session['user_id']))
        g.db.commit()
        for k,v in request.form.iteritems():
            session[k] = v
    return render_template('profile.html')

    
def get_user_id(username):
    if username == 'favicon.ico':       
        return None
    """Get the userid of the username"""
    prepared_statement = """
    select id from user where username="{}"
    """.format(username)
    return g.db.execute(prepared_statement).fetchone()[0]


@app.route('/tweets/<int:tweet_id>/delete', methods=['POST'])
@login_required 
def delete_tweet(tweet_id):
    cur = g.db.execute('SELECT * from tweet where user_id=?', (tweet_id,))
    if len(cur.fetchall()) < 2:
        flash("Sorry, you must have at least two tweets in order to delete one")
        return redirect(request.script_root)
    g.db.execute('DELETE FROM tweet WHERE id=?',(tweet_id,))
    g.db.commit()
    flash("Tweet deleted successfully")
    return redirect(request.script_root)