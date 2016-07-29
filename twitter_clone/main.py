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
            query = "SELECT id, username from user WHERE username = ? AND password = ?"
            cursor = g.db.execute(query, (username, password))
            #cursor = g.db.execute(query, (username, hashedPassword))
            results = cursor.fetchall()
            user_id = results[0][0]
            username = results[0][1]
            session["logged_in"] = True
            session["user_id"] = user_id
            session["username"] = username
            return redirect("/own_feed/")
            #return "your user id is {}".format(id)
        except:
            return redirect("/login/")
            # return "you are wrong {}".format(results)


@app.route("/own_feed/", methods = ["GET", "POST"])
@login_required
def own_feed():
    if request.method == 'GET':
        query = "SELECT id, created, content FROM tweet WHERE user_id = ? ORDER BY created desc"
        cursor = g.db.execute(query, (session['user_id'],))
        tweets = _retrieve_tweets(session['user_id'])
        return render_template('own_feed.html', tweets=tweets)
    if request.method == 'POST':
        #check if tweet is less than 140 chars, otherwise spit a message
        _post_tweet(session['user_id'], request.form['tweet'])
        # want to upload request.form['tweet'] = tweet text, need user_id that posted it
        tweets = _retrieve_tweets(session['user_id'])
        return render_template('own_feed.html', tweets=tweets)
        
        
        #query = "INSE"
# CREATE TABLE tweet (
#   id INTEGER PRIMARY KEY autoincrement,
#   user_id INTEGER,
#   created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#   content TEXT NOT NULL,
#   FOREIGN KEY(user_id) REFERENCES user(id),
#   CHECK(
#       typeof("content") = "text" AND
#       length("content") <= 140
#   )

# INSERT INTO "tweet" ("user_id", "content") VALUES (12, "I love DOGE");
def _post_tweet(user_id, tweet_text):
    query = 'INSERT INTO "tweet" ("user_id", "content") VALUES (?, ?)'
    g.db.execute(query, (user_id, tweet_text))
    
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