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

# login view
@app.route('/login', methods=['GET'])
def login():
    return render_template("static_templates/login.html")
    
@app.route("/process_login", methods=['POST'])
def process_login():
    username = request.form['username']
    password = request.form['password']
    
    cursor = g.db.execute("SELECT * from user WHERE username=?", username)
    user_from_db = cursor.fetchone()
    print(cursor)
    password_from_db = user_from_db[2]
    hashed_passwd = md5(password[0].encode('utf-8')).hexdigest()
    
    if hashed_passwd == password_from_db:
        session["username"] = username
        session["user_id"] = user_from_db[0]
        flash("You are correctly logged in")
        return redirect("/")
    else:
        flash("Invalid username or password")
    
    
    return render_template("login.html", next="/")

    
@app.route('/')
@login_required
def home():
    if 'username' in session:
        return redirect('/{}'.format(session['username']))
    else:
        return
    
    
@app.route('/logout')
@login_required
def logout():
    next = request.args.get('next', '/')
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(next)
    
@app.route('/<username>', methods=['GET', 'POST'])
def twitter_feed(username):
    pass


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'GET':
        logged_in_username = session['username']
        # logged_in_username = ("chepkeitany", )
        cursor = g.db.execute("SELECT username, first_name, last_name, birth_date from user WHERE username=?", logged_in_username)
        username, first_name, last_name, birth_date = cursor.fetchone()
        
        return render_template('dyn_profile.html', username=username, first_name=first_name, last_name=last_name, birth_date=birth_date)

    elif request.method == 'POST':
        params = {
            'first_name': request.form['first_name'],
            'last_name': request.form['last_name'],
            'birth_date': request.form['birth_date'],
            'username': session['username']
        }
        print("USERNAME TYPE")
        print(type(params['username']))
        # update database with new values
        try:
            cursor = g.db.execute("UPDATE user SET first_name=:first_name, last_name=:last_name, birth_date=:birth_date WHERE username=:username;", params)
            g.db.commit()
            # cursor = g.db.execute("UPDATE user SET first_name=?, last_name=?, birth_date=? WHERE username=?", (params['first_name'], params['last_name'], params['birth_date'], params['username']))
            
        except sqlite3.IntegrityError:
            print("follow the rules yo!")
            
            
        post_cursor = g.db.execute("SELECT username, first_name, last_name, birth_date from user WHERE username=?", session['username'])
        username, first_name, last_name, birth_date = post_cursor.fetchone()
            
        return render_template('dyn_profile.html', username=username, first_name=first_name, last_name=last_name, birth_date=birth_date)