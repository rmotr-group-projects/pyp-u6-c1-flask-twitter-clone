import sqlite3
from hashlib import md5
from functools import wraps
from flask import Flask
from flask import (g, request, session, redirect, render_template,
                   flash, url_for, abort)


app = Flask(__name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:################################session
            return redirect(url_for('login', next=request.url), code=302)
        return f(*args, **kwargs)
    return decorated_function


# implement your views here
#login in/out views
@app.route('/')
@login_required
def homepage():
    return render_template('own_feed.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    error = None
    if request.method == 'POST':
        x = valid_login(request.form['username'], "{}".format(md5(request.form['password']).hexdigest()))
        if x:
            #log_the_user_in(request.form['username'])
            session['username'] = request.form['username']
            session['user_id'] = x
            return redirect(url_for('homepage'), code=302)
        else:
            error = 'Invalid username or password'
            flash(error, category='message')
    if request.method == 'GET' and session:
        return redirect(url_for('homepage'))
    # the code below is executed if the request method  was GET or the credentials were invalid
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop("username", None)
    session.pop('user_id', None)
    return redirect(url_for('homepage'))

#tweet views here
@app.route('/<username>', methods=['GET', 'POST'])
def user_feeds(username):
    id = convert_username_to_id(username)
    if request.method == 'POST':
        if 'username'not in session:
            abort(403)
        if username != session['username']:
            abort(403)
        new_tweet = str(request.form['tweet'])
        #print('this is the new tweet,', new_tweet)
        string='INSERT INTO tweet ("user_id", "content") VALUES (%s, "%s");'%(id, new_tweet)
        #print('this is the string', string)
        g.db.execute(string)
    tweets = get_tweets(id)
    if session:
        if session['username'] == username:
            print(1, tweets)
            return render_template('own_feed.html', username=username, tweets=tweets)
        else:
            print(2, tweets)
            return render_template('other_feed.html', username=username, tweets=tweets)
    else:
        print(3, tweets)
        return render_template('other_feed.html', username=username, tweets=tweets)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        username = str(request.form['username'])
        first_name = str(request.form['first_name'])
        last_name = str(request.form['last_name'])
        birth_date = str(request.form['birth_date'])
        a_string = 'UPDATE user  SET username="%s" , first_name="%s", last_name="%s",\
         birth_date="%s" where id=%s;'%(username, first_name, last_name, birth_date, session['user_id'])
        print (a_string)
        g.db.execute(a_string)
    string = 'SELECT * FROM user where id = %s' % session['user_id']
    curs = g.db.execute(string).fetchall()
    print(curs)
    return render_template('profile.html', username=curs[0][1], firstname=curs[0][3],\
            lastname=curs[0][4], birthdate=curs[0][5])

@app.route('/tweets/<int:id>/delete', methods=['GET', 'POST'])
@login_required
def delete(id):
    print('this is the id of tweet:', id)
    cursor = g.db.execute("select * from tweet;")
    print(cursor.fetchall())

    string = 'DELETE FROM tweet WHERE id=%s' % id
    g.db.execute(string)

    cursor = g.db.execute("select * from tweet;")
    print(cursor.fetchall())

    return redirect(url_for('homepage'))


def convert_username_to_id(username):
    users_cursor = g.db.execute('SELECT * FROM user')
    users_data = users_cursor.fetchall()
    for x in users_data:
        if username in str(x):
            return x[0]

def get_tweets(id):
    tweets_cursor = g.db.execute('SELECT * FROM tweet')
    tweets_data = tweets_cursor.fetchall()
    tweets_list=[]
    for x in tweets_data:
        if id == x[1]:
            tweets_list.append(x)
    return tweets_list


#database operations
def connect_db(db_name):
    return sqlite3.connect(db_name)


@app.before_request
def before_request():
    g.db = connect_db(app.config['DATABASE'][1])

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


def valid_login(par, param):
    #curs = g.db.cursor()
    users_cursor = g.db.execute('SELECT * FROM user')
    users_data = users_cursor.fetchall()
    for x in users_data:
        if par in x and param in x:
            return x[0]
    return False
