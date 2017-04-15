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


@app.route('/', methods=['GET'])
def homepage():
    if 'username' in session:
        return render_template('dynamic_templates/own_feed.html')
    return redirect('/login')
 
 
@app.route('/login', methods=['GET', 'POST'])
def login():
    next = request.args.get('next', '/')
    if request.method == 'GET':
        if 'username' in session:
            return redirect(next)
        return render_template('dynamic_templates/login.html')
            
    if request.method == 'POST':
        username = request.form['username']
        password = md5(request.form['password'].encode('utf-8')).hexdigest()
        c = g.db.execute(
            "SELECT id, username, password FROM user WHERE username=?;",
            (username,))
        user = c.fetchone()
        if user and user[2] == password:
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(next)
        flash('Invalid username or password')
        return render_template('dynamic_templates/login.html', next=next)
    
    
@app.route('/logout')
def logout():
    next = request.args.get('next', '/')
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(next)
            
            
@app.route('/profile', methods=['GET', 'POST'])
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
            'last_name': request.form['last_name'],
            'birth_date': request.form['birth_date'],
            'username': request.form['username']
        }
        g.db.execute(query, params)
        g.db.commit()
        flash("Your profile was successfully updated.")
        
    c = g.db.execute(
    "SELECT username, first_name, last_name, birth_date FROM user WHERE id=?",
    (session['user_id'],))
    user = c.fetchone()
    pfl = {'username': user[0], 'first_name': user[1],
           'last_name': user[2], 'birth_date': user[3]}
    return render_template('dynamic_templates/profile.html', profile=pfl)
                     

@app.route('/<username>', methods=['GET', 'POST'])
def feed(username):
    feed_get_sql = """
        SELECT u.username, t.id, t.created, t.content
        FROM user u INNER JOIN tweet t ON (u.id=t.user_id)
        WHERE u.username=:username ORDER BY datetime(t.created) DESC;
        """
    if session.get('username', None) == username:
        if request.method == 'POST':
            query = """
            INSERT INTO tweet ("user_id", "content") 
            VALUES (:user_id, :content);
            """
            params = {'user_id': session['user_id'],
                      'content': request.form['tweet']}
            g.db.execute(query, params)
            g.db.commit()
        c = g.db.execute(feed_get_sql, {'username': username})     
        tweets = [dict(username=row[0], id=row[1], created=row[2], 
                       content=row[3]) for row in c.fetchall()]
        return render_template('dynamic_templates/own_feed.html', tweets=tweets)
        
    else:
        if request.method == 'POST':
            return redirect('/', 403)
        c = g.db.execute(feed_get_sql, {'username': username})  
        tweets = [dict(username=row[0], id=row[1], created=row[2], 
                  content=row[3]) for row in c.fetchall()]
        return render_template('dynamic_templates/other_feed.html', 
                               tweets=tweets)
        
@app.route('/tweets/<int:tweet_id>/delete', methods=['POST'])
@login_required
def delete_tweet(tweet_id):
    next = request.args.get('next', '/')
    cursor = g.db.execute(
        "SELECT id FROM tweet WHERE id=? AND user_id=?;",
        (tweet_id, session['user_id']))
    tweet = cursor.fetchone()
    
    if tweet:
        g.db.execute('DELETE FROM tweet WHERE id=?;', (tweet_id,))
        g.db.commit()
        return redirect(next, 302)
    return redirect(next, 404)
