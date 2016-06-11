import sqlite3
import datetime
from hashlib import md5
from functools import wraps
from flask import Flask
from flask import (g, request, session, redirect, render_template,
                   flash, url_for, abort)
from settings import DATABASE_NAME

app = Flask(__name__)
db_name = DATABASE_NAME

def connect_db(db_name):
    return sqlite3.connect(db_name)


@app.before_request
def before_request():
    g.db = connect_db(app.config['DATABASE'][1])

#login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


# implement your views here
@app.route("/", methods=["GET"])
def index():
    #check if logged in
    if "username" in session and session["username"]:
        return redirect("/{}".format(session["username"]))
    return redirect(url_for("login"))



@app.route("/login", methods=["GET", 'POST'])
def login():
    if request.method == 'POST':
        return authenticate(request.form["username"], request.form["password"])
    else:
        """if "logged_in" in session and session["logged_in"] == True:
            return redirect(url_for("index"))"""
        return render_template('/static_templates/login.html')
    
def authenticate(username, password):
    password = md5(password).hexdigest() #Hash it
    
    conn = connect_db(db_name) #Connect to DB
    cursor = conn.cursor()
    cursor.execute("select * from user where username = ?", (username, ) )
    user = cursor.fetchone() #Fetch the user
    if user:
        if password == user[2]:
            print(user[2])
            #Take advantage of the global variable session, to store some user-related stuff that's gonna be useful
            session["logged_in"] = True
            session["username"] = user[1]
            session['user_id'] = user[0]
            #redirect
            return redirect("/{}".format(session["username"]))
        else:
            return "Invalid password"
    else:
        return "Invalid username or password"
        
    
#Lets have a logout function that handles clicks to the logout button
@app.route("/logout")
def logout():
    session["username"] = ""
    session['user_id'] = ""
    session["logged_in"] = False
    return redirect(url_for("login"))


@app.route("/tweets/<id>/delete", methods=["DELETE", "POST"]) #Not sure what method we-re using, I added delete and post for now.
@login_required
def delete(id): #I changed this from tweet_id to just id, to comply with the changes you made in the decorator call
    try:
        int(id)
    except:
        abort(404)
        
    conn = connect_db(db_name) #Connect to DB
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tweet WHERE id=?", (id, ))
    tweets = cursor.fetchall()
    print(tweets)
    if tweets:
        cursor.execute("DELETE FROM tweet WHERE id=?", (id, ) )
        conn.commit() #We were missing a commit call
    
        """After deletion, redirect back to the tweet feed """
        return redirect("/{}".format(session["username"]))
    else:
        abort(404)



@app.route("/<username>", methods =["GET","POST"])
@login_required
def own(username):
    if request.method == "GET":
        conn = connect_db(db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tweet where user_id = ?", (session['user_id'], ) ) #Take advantage of the userid entry we stored in global session
        tweets = cursor.fetchall()
        return render_template('static_templates/own_feed.html', tweets=tweets)
    else:
        if request.form["tweet"]:
            conn = connect_db(db_name) #Connect to DB
            cursor = conn.cursor()
            current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT into tweet(user_id, created, content) VALUES(?, ?, ?)", (session['user_id'], current_date, request.form["tweet"]))
            conn.commit()
        #refresh page
        return redirect("/{}".format(session["username"]))
        
@app.route("/other/<username>")
def get_feed(username):
    if username == session["username"]:
        return redirect("/{}".format(session["username"]))
    else:
        conn = connect_db(db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT id from user WHERE username=?", (username, ))
        otherid = cursor.fetchone()[0]
        print(otherid)
        cursor.execute("SELECT * from tweet WHERE user_id = ?", (otherid, ))
        othertweets = cursor.fetchall()
        return render_template('static_templates/other_feed.html', tweets=othertweets, username=username)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "GET":
        conn = connect_db(db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user WHERE id = ?", (session['user_id'], ))
        user = cursor.fetchone()
        return render_template('/static_templates/profile.html', user=user)
    else:
        conn = connect_db(db_name) #Connect to DB
        cursor = conn.cursor()
        cursor.execute("UPDATE user SET first_name=?, last_name=?, birth_date=? WHERE id=?", (request.form["first_name"], request.form["last_name"], request.form["birth_date"], session['user_id']))
        conn.commit()
        return redirect(url_for("profile"))
    
@app.route("/other", methods=["GET"])
def other():
    return render_template('static_templates/other_feed.html')
    


