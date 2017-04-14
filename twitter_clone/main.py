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
@app.route('/login', methods = ['POST', 'GET'])
def login():
    if request.method == 'GET':
        if 'username' in session:
            return redirect('/')
        else:
            return render_template('static_templates/login.html')
    if request.method == 'POST':
        username = request.form['username']
        password = md5(request.form['password'].encode('utf-8')).hexdigest()
        cursor = g.db.execute(
            "SELECT id, username FROM user WHERE username=:username and password=:password;",
            {'username':username,'password':password})
        user = cursor.fetchone()
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect('/')
        else:
            flash('Invalid username or password')
            return render_template('static_templates/login.html')

@app.route('/')
@login_required
def home():
    return render_template('static_templates/own_feed.html')

@app.route('/logout')
def logout():
    session.pop('user_id')
    session.pop('username')
    return redirect('/')
    
@app.route('/profile', methods = ['POST', 'GET'])
@login_required
def profile():
    if request.method == 'POST':
        query = """
        UPDATE user
        SET first_name=:first_name, last_name=:last_name, birth_date=:birth_date
        WHERE username=:username;
        """
        params = {
        'first_name': request.form['first_name'],
        'last_name': request.form['last_name'] , 
        'birth_date': request.form['birth_date'],
        'username': request.form['username']
        }
        g.db.execute(query,params)
        g.db.commit()
        flash("Your profile was correctly updated")
        
    cursor = g.db.execute(
            "SELECT username, first_name, last_name, birth_date FROM user WHERE id=:id",
            {'id':session['user_id']})
    user = cursor.fetchone()
    _profile = {'username':user[0], 'first_name': user[1], 'last_name': user[2], 'birth_date': user[3]}
    return render_template('static_templates/profile.html', profile=_profile)

@app.route('/<username>', methods=['POST', 'GET'])
def feed(username):
    if session.get('username',None) == username:
        if request.method == 'POST':
            query = 'INSERT INTO tweet ("user_id", "content") VALUES (:user_id, :content);'
            params = {'user_id': session['user_id'], 'content': request.form['tweet']}
            g.db.execute(query, params)
            g.db.commit()
            
        cursor = g.db.execute("""
        SELECT 
        u.username, t.id, t.created, t.content
        FROM user u INNER JOIN tweet t ON u.id = t.user_id
        WHERE username=:username;
        """,{'username':username})
        tweets = [dict(username=c[0],id=c[1],created=c[2], content=c[3]) for c in cursor.fetchall()]
        return render_template('static_templates/own_feed.html',tweets=tweets)
    
    else:
        if request.method == 'POST':
            return redirect('/',403)
        cursor = g.db.execute("""
        SELECT 
        u.username, t.id, t.created, t.content
        FROM user u INNER JOIN tweet t ON u.id = t.user_id
        WHERE username=:username;
        """,{'username':username})
        tweets = [dict(username=c[0],id=c[1],created=c[2], content=c[3]) for c in cursor.fetchall()]
        return render_template('static_templates/other_feed.html',tweets=tweets)
    

@app.route('/tweets/<int:tweet_id>/delete',methods=['POST'])
@login_required
def delete_tweet(tweet_id):
    cursor = g.db.execute("SELECT id,user_id from tweet WHERE id=:tweet_id;",{'tweet_id':tweet_id})
    tweet = cursor.fetchone()
    
    if tweet:
        if session['user_id'] == tweet[1]:
            g.db.execute('DELETE FROM tweet WHERE id=:tweet_id;', {'tweet_id':tweet_id})
            g.db.commit()
            return redirect('/',302)
    return redirect('/',404)
    
    
    	
