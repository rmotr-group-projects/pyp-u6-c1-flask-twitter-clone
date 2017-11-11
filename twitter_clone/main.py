import sqlite3
from hashlib import md5
from functools import wraps
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
def index():
    return ""
    
@app.route('/<string:username>', methods=['GET', 'POST'])
def feed(username):
    
    if request.method == 'POST':
        if 'username' not in session:
            abort(403)
        
        content = request.form['tweet']
        params = {'user_id' : session['user_id'], 'content' : content}
        cursor = g.db.execute("""
            INSERT INTO tweet (user_id, content) VALUES
            (:user_id, :content);
        """, params)
        g.db.commit()
    
    params = {'username' : username}
    cursor = g.db.execute("""
        SELECT t.id, u.username, t.created, t.content
        FROM tweet t INNER JOIN user u ON t.user_id = u.id
        WHERE u.username = :username;
    """, params)
    tweets = [dict(id=row[0], username=row[1], created=row[2], content=row[3])
               for row in cursor.fetchall()]
    
    return render_template('static_templates/own_feed.html', tweets=tweets)

@app.route('/tweets/<int:tweet_id>/delete', methods=['POST'])
@login_required
def tweets(tweet_id):
    params = {'id' : tweet_id }
    
    cursor = g.db.execute('SELECT * FROM tweet WHERE id = :id;', params)
    tweet = cursor.fetchone()
    if not tweet:
        abort(404)
    
    g.db.execute('DELETE FROM tweet WHERE id = :id;', params)
    g.db.commit()
    return redirect('/')
    
@app.route('/profile', methods=['POST', 'GET'])
@login_required
def profile():
    if request.method == 'POST':
        first_name = request.form['first_name'].strip()
        last_name = request.form['last_name'].strip()
        birth_date = request.form['birth_date'].strip()
        params = {
            'id': session['user_id'],
            'first_name': first_name,
            'last_name' : last_name,
            'birth_date' :birth_date
        }
        g.db.execute('UPDATE user SET first_name = :first_name, last_name = :last_name, birth_date = date(:birth_date) WHERE id = :id;', params)
        g.db.commit()
        
    return render_template('static_templates/profile.html')   

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'GET':
        if 'username' in session:
            return redirect('/')
        else:
            return render_template('static_templates/login.html')
    elif request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        params = {
            'username': username,
            'password': md5(password.encode('utf-8')).hexdigest()
        }
        cursor = g.db.execute('SELECT * FROM user WHERE username = :username AND password = :password;', params)
        user = cursor.fetchone()
        if user:
            session['username'] = username
            session['user_id'] = user[0]
        else:
            return "Invalid username or password", 200
        return redirect('/')
        
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect('/')
        