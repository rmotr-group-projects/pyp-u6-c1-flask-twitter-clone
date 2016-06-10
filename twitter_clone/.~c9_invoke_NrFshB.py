import sqlite3
from hashlib import md5
from functools import wraps
from hashlib import md5
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
@app.route('/')
@login_required
def feed():
    # if the user is NOT logged in: redirect to /login
    # if the user IS logged in, redirect to: /<username>
   
    return redirect(url_for('user_profile', user=session['username']))
    
@app.route('/login', methods=['POST', 'GET'])
def login():
    next_url = request.args.get('next', '/')
    
    if 'username' in session:
        return redirect(next_url)
    
    if request.method == 'GET':
        return render_template("static_templates/login.html",error=False)
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password = md5(password).hexdigest()

        cursor = g.db.execute("SELECT id, username, password FROM user")
        entries = [dict(user_id=row[0], name=row[1], password=row[2]) for row in cursor.fetchall()]
        
        for dictionary in entries:
            if dictionary['name'] != username or dictionary['password'] != password:
                error = "Invalid username or password"
            else:
                session['user_id'] = dictionary['user_id']
                session['username'] = username
                
                return redirect(next_url)
        return render_template("static_templates/login.html", error=error)
        
@app.route('/logout')
@login_required
def logout():
    session.pop('username')
    session.pop('user_id')
    flash('You were logged out')
    return redirect(url_for('feed'))
    

@app.route('/<user>', methods = ['POST', 'GET'])
def user_profile(user):
    #g.db.execute("INSERT INTO tweet (content) VALUES (?)", (tweet_content,))
    if request.method == 'POST' :
        if "username" in session and session["username"] == user:
            tweet_content = request.form['tweet']
        g.db.execute("INSERT INTO tweet (user_id, content) VALUES (:t)", (user_id, tweet_content))
            g.db.execute("INSERT INTO tweet (user_id, content) VALUES (:user_id , :content)", {"user_id" : user_id, "content" : tweet_content})
            g.db.commit()
        else:
            abort(403)
        
    content = get_user_content(user)
    
    if content is None:
        return "User does not exist"
    elif "username" in session and session["username"] == user:
        return render_template("static_templates/own_feed.html", tweets=content, ow)
    else:
        return render_template("static_templates/user_tweets.html", tweets=content, user=user)
    

def get_user_content(user):
    cursor = g.db.execute("SELECT id, username FROM user WHERE username = (?)", (user,))
    lst = cursor.fetchall()
    
    if not lst:
        return None
        
    user_id = lst[0][0]
    cursor = g.db.execute("SELECT created, content FROM tweet WHERE user_id = (?)", (user_id,))
    content = [dict(created=row[0], content=row[1]) for row in cursor.fetchall()]
    
    return content 
     