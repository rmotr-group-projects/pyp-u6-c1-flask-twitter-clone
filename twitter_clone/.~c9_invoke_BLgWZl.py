import sqlite3
from hashlib import md5
from functools import wraps
from flask import Flask
from flask import (g, request, session, redirect, render_template,
                   flash, url_for,abort)

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
@app.route('/')
def landing():
    if 'username' not in session:
        return redirect(url_for('login'))
    else:
        return render_template('static_templates/own_feed.html')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    url_redirect = request.args.get('next','/')
    
    if 'username' in session:
        return redirect(url_redirect)
    
    if request.method == 'POST':
            password = request.form['password']
        username = request.form['username']
        pwhash = md5(password.encode('utf-8')).hexdigest()
        
        #get user data from DB
        sql_query="select id, password from user where username = :username;"
        cursor = g.db.execute( sql_query, {'username': username})
        # [[user, password], [user,password]]
        db_users = cursor.fetchone()
        #authenticate
        if db_users is not None and pwhash == db_users[1]:
            session['user_id'] = db_users[0]
            session['username'] = username
            return redirect(url_redirect)
            
        flash('Invalid username or password')
        return redirect('/login')
        
    return render_template('static_templates/login.html', next = url_redirect)

@app.route('/profile')
@login_required
def edit_profile():
    # 
    pass
  

@app.route('/feed')
def insert_feed():
    #read only mode
    #session.pop
    pass

@app.route('/logout')
@login_required
def logout():
    # next_url = request.args.get('next', '/')
    # session.pop('user_id')
    # session.pop('username')
    # return redirect(next_url)
    pass