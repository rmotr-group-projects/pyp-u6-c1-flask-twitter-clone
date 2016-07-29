import sqlite3
from hashlib import md5
from functools import wraps
from flask import Flask
from flask import (g, request, session, redirect, render_template,
                   flash, url_for)

app = Flask(__name__)


def connect_db(db_name):
    return sqlite3.connect(db_name)

def _hash_password(password):
    """
    Uses md5 hashing for now
    """
    return md5(password.encode("utf-8").hexdigest())
    
#def _collect_tweet(user_id):
#    


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

#to add our current directory to pythonpath
#PYTHONPATH=. python twitter_clone/runserver.py

# implement your views here
@app.route("/login/", methods = ["GET", "POST"])
def login():
    """
    Log in page
    """
    if request.method == 'GET':
        return render_template('login.html')
    
    elif request.method == "POST":
        
        username = request.form["username"]
        password = request.form["password"]
        #hashedPassword = _hash_password(password)

        #cursor = g.db.cursor()
        #Parametetrize SQL queries to prevent sql injection
        try:
            query = "SELECT id from user WHERE username = ? AND password = ?"
            cursor = g.db.execute(query, (username, password))
            #render_template("own_fee")
            results = cursor.fetchall()
            user_id = results[0][0] # <------
            session["logged_in"] = True
            session["user_id"] = user_id
            session["user_name"] = username
            return redirect("/own_feed/")
            #return "your user id is {}".format(id)
        except:
            return redirect("/login/")
            # return "you are wrong {}".format(results)

@login_required        
@app.route("/own_feed/", methods = ["GET", "POST"])
def own_feed():
    if request.method == 'GET':
        query = "SELECT id, created, content FROM tweet WHERE user_id = ? ORDER BY created desc"
        cursor = g.db.execute(query, (session['user_id'],))
        tweets = _retrieve_tweets(session['user_id'])
        return render_template('own_feed.html', tweets=tweets)

def _retrieve_tweets(user_id):
    query = "SELECT id, created, content FROM tweet WHERE user_id = ? ORDER BY created desc"
    cursor = g.db.execute(query, (user_id,))
    tweets = [dict(user_id = row[0], created = row[1], content = row[2]) for row in cursor.fetchall()]
    return tweets
    
@app.route("/other_feed/", methods = ['GET', 'POST'])
def other_feed():
    if request.method == 'GET':
        return render_template('other_feed.html')
    
@app.route("/logout/")
def logout():
    session.pop
    


@app.route('/')
#@login_required()
def homepage():
    return "Hello world"


if __name__ == "__main__":
    app.run()