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
   
    return redirect(url_for('show_tweets', user=session['username']))
    
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
        password = md5(password.encode('utf-8')).hexdigest()

        cursor = g.db.execute("SELECT id, username, password FROM user")
        entries = [dict(user_id=row[0], name=row[1], password=row[2]) for row in cursor.fetchall()]
        
        for dictionary in entries:
            if dictionary['name'] != username or dictionary['password'] != password:
                error = "Invalid username or password"
            else:
                session['user_id'] = dictionary['user_id']
                session['username'] = username
                flash("You have been logged in")
                
                return redirect(next_url)
        return render_template("static_templates/login.html", error=error)
        
        
@app.route('/logout')
@login_required
def logout():
    session.pop('username')
    session.pop('user_id')
    flash('You were logged out')
    return redirect(url_for('feed'))
    

@app.route('/<user>', methods = ['POST'])
def post_tweet(user):
    if "username" in session and session["username"] == user:
        tweet_content = request.form['tweet']
        user_id = session["user_id"]
        
        if len(tweet_content) <= 140:
            g.db.execute("INSERT INTO tweet (user_id, content) VALUES (:user_id , :content)", {"user_id" : user_id, 
                                                                                               "content" : tweet_content})
            g.db.commit()
            flash("Tweet posted")
            
        return show_tweets(user)
    else:
        abort(403)

@app.route('/<user>', methods = ['GET'])
def show_tweets(user):
    content = get_tweet_content(user)
    own_tweets = False
    username = session["username"] if "username" in session else ""
    
    if content is None:
        return "User does not exist"
    elif "username" in session and session["username"] == user:
        own_tweets=True
        username = session["username"]
        
    return render_template("static_templates/own_feed.html", tweets=content, 
                                                             own_tweets=own_tweets, 
                                                             username=username, 
                                                             logged_in = "username" in session)
    
     
@app.route('/profile', methods = ['POST', 'GET'])
@login_required
def user_profile():
    username = session['username']
    user_id = session['user_id']
    
    if request.method == 'POST' :
        data = ( request.form['first_name'], request.form['last_name'], request.form['birth_date'], user_id )

        g.db.execute("UPDATE user SET first_name=?, last_name=?, birth_date =? WHERE user.id=?", data)
        g.db.commit()
        flash("Profile Updated")
        
    
    cursor = g.db.execute("SELECT first_name, last_name, birth_date FROM user WHERE id = (?)", (user_id,))
    first_name, last_name, birth_date = tuple(cursor.fetchall()[0])
    

    return render_template("static_templates/profile.html", first_name = first_name, 
                                                            last_name = last_name, 
                                                            birth_date = birth_date, 
                                                            username = username)
    
@app.route('/tweets/<tweet_id>/delete', methods = ['POST'])
def delete_tweet(tweet_id): 
  
    if not str(tweet_id).isdigit():
        abort(404)
    
    if "username" not in session:
        return redirect("login")
    
    g.db.execute("DELETE FROM tweet WHERE id=?", (tweet_id,))
    g.db.commit()
    flash("Tweet deleted")
    
    return redirect('/')
    
    
def get_tweet_content(user):
    cursor = g.db.execute("SELECT id, username FROM user WHERE username = (?)", (user,))
    lst = cursor.fetchall()
    
    if not lst:
        return None
        
    user_id = lst[0][0]
    cursor = g.db.execute("SELECT created, content, id FROM tweet WHERE user_id = (?) ORDER BY created desc", (user_id,))
    content = [dict(created=row[0], content=row[1], tweet_id=row[2]) for row in cursor.fetchall()]
    
    return content 
     