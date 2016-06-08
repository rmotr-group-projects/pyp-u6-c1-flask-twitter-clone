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
def home():
    return redirect(url_for('login'))
    

@app.route('/login', methods=['POST', 'GET'])
def login():
    error = None
    '''
    if request.method == 'GET':
        return render_template('login.html')
    '''
    if request.method == 'POST':
        # check if username in database, not get all users
        # request.form is dict with all the data from POST
        # request.form[user], request.form[password]
        cur = g.db.execute('SELECT username, password FROM user WHERE username=?'\
        ,(request.form['username'],))
        user = cur.fetchone()
        if user:
            if request.form['password'] != user[1]:
                error = 'Invalid password'
            else:
                session['username'] = user[0]
                return redirect(url_for('own_feed'))
                #return render_template('own_feed.html')
        else:
            error = 'Invalid username'
        return error
    return render_template('login.html')
        
        
    '''
        cur = g.db.execute\
        ('SELECT username, password FROM user'\
        'WHERE username={0}, password={1}'.\
        format(request.form['username'], request.form['password']))
        user = cursor.fetchone()
        
        
        if user:
            return url_for('profile.html', user=user)
    '''

@app.route('/logout') #add variable username
@login_required
def logout():
    pass

@app.route('/own_feed') #add variable username
@login_required
def own_feed():
    
    pass
    





