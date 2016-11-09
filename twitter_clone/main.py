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


# implement your views here
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    cursor_pw = g.db.execute('SELECT username, password FROM user;')
    cursor_id = g.db.execute('SELECT username, id FROM user;')
    users_pw = dict(cursor_pw.fetchall())
    users_id = dict(cursor_id.fetchall())
    
    if request.method == 'POST': # someone's trying to log in

        username = request.form['username']
        password = request.form['password']
        hashed_pw = md5(request.form['password'].encode('utf-8')).hexdigest()
        
        if username in users_pw:
            if users_pw[username] == hashed_pw:
                session['user_id'] =  users_id[username]
                session['username'] = username
                return redirect(url_for('index'), code=302)
                # return redirect(url_for('index'))
        else:
            error = "Invalid username or password"

    return render_template('login.html', error=error)
    
@app.route('/')
@login_required
def index():
    return redirect(url_for('login'))
    
@app.route('/logout')
def logout():
    # second parameter means that nothing will happen if the key doesn't exist
    session.pop('user_id', None)
    session.pop('username', None) 

    return redirect(url_for('index'))
    

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    username = session['username']
    if request.method == 'GET':
        # get all the tweets
        pass
    elif request.method == 'POST':
        birth_date = request.form['birth_date']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        raw_sql = '''
            UPDATE user 
            SET birth_date = '{}', first_name = '{}', last_name = '{}' 
            WHERE username = '{}'
        '''.format(birth_date, first_name, last_name, session['username'])
        
        g.db.execute(raw_sql)
        g.db.commit()
        
    return render_template('profile.html', username = username)

# for passing parameters `<int:` makes sure the param is an integer
# @app.route('/page/<page_id>')
# def page(page_id):
#     pageid = page_id

@app.route('/tweets/<int:tweet_id>/delete')
def delete(tweet_id):
    import ipdb; ipdb.set_trace()
    print('test')
    print(request)
    
    if 2 > 1: # if authenticated (ie: the user owns the tweet)
        raw_sql = 'DELETE FROM tweet WHERE tweet.id = {}'.format(tweet_id)
        return redirect(url_for('index'))
    else: # not authenticated
        return redirect(url_for('login'))

@app.route('/<username>', methods=['GET', 'POST'])
def own_feed(username):
    if session != {}:
        username = session['username']
        user_id = session['user_id']
        
        if request.method == 'GET':
            raw_sql = '''
                SELECT u.username, t.content
                FROM tweet t
                LEFT JOIN user u on t.user_id = u.id
                '''
            g.db.execute(raw_sql)
        
        if request.method == 'POST':
            # check user is authenticated
            # if yes, post a tweet
            tweet = request.form['tweet']
            raw_sql = '''
            INSERT INTO tweet(user_id, created, content)
            VALUES({},{},{})
            '''.format(user_id, 'current_timestamp', tweet)
        
            
    return render_template('own_feed.html', session=session)
                 
        