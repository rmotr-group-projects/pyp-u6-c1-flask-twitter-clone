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
@login_required
def index():
    if 'username' in session:
        return render_template('static_templates/own_feed.html')
    

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'GET': 
        if 'username' in session:
            return redirect('/')
        else:
            return render_template('static_templates/login.html')
            
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hash_password = md5(password.encode('utf-8')).hexdigest()
        cursor = g.db.execute('SELECT id, username, password FROM user WHERE username=:username',
            {'username': username})
        user = cursor.fetchone()
        
        if user:
            if user[2] == hash_password:
                session['user_id'] = user[0]
                session['username'] = user[1]
                flash('Successful Login')
                return redirect('/')
        
        flash('Invalid username or password')
        return render_template('static_templates/login.html')
        
            


@app.route('/logout')
def logout():
    session.pop('username')
    session.pop('user_id')
    return redirect('/')
    
@app.route('/profile', methods=['POST', 'GET'])
@login_required
def profile():
    if request.method == 'POST':
        query = """
            UPDATE user
            SET first_name=:first_name, last_name=:last_name, birth_date=:birth_date
            WHERE username=:username;
        """
        parameters = {
            'first_name': request.form['first_name'],
            'last_name': request.form['last_name'],
            'birth_date': request.form['birth_date'],
            'username': request.form['username']
        }
        g.db.execute(query, parameters)
        g.db.commit()
        flash('Your profile was correctly updated')
    
    cursor = g.db.execute(
            'SELECT username, first_name, last_name, birth_date FROM user WHERE id=:id',
            {'id':session['user_id']})
    username, first_name, last_name, birth_date = cursor.fetchone()
    
    return render_template('static_templates/profile.html', 
            username=username, first_name=first_name, last_name=last_name, birth_date=birth_date)

@app.route('/<username>', methods=['POST', 'GET'])
def feed(username):
    if request.method == 'POST':
        if 'username' not in session:
             return redirect('/', 403)
        
        query = 'INSERT INTO tweet ("user_id", "content") VALUES (:user_id, :content);'
        params = {'user_id': session['user_id'], 'content': request.form['tweet']}
        g.db.execute(query, params)
        g.db.commit()
    
    cursor = g.db.execute("""
                SELECT t.id, u.username, t.created, t.content
                FROM tweet t INNER JOIN user u ON t.user_id=u.id
                WHERE u.username=:username;
                """, {'username':username})
    tweets = [dict(id=row[0], username=row[1], created=row[2], content=row[3])
                 for row in cursor.fetchall()]
    
    if session.get('username', None) == username:
        return render_template('static_templates/own_feed.html', tweets=tweets)
    
    else:
        return render_template('static_templates/other_feed.html', tweets=tweets)


@app.route('/tweets/<int:tweet_id>/delete',methods=['POST'])
@login_required
def delete_tweet(tweet_id):
    cursor = g.db.execute("SELECT id, user_id FROM tweet WHERE id={}".format(tweet_id))
    record = cursor.fetchone()
 	
    if record:
        g.db.execute('DELETE FROM tweet WHERE id=:tweet_id;',{'tweet_id':tweet_id})
        g.db.commit()
        return redirect('/', 302)
    return redirect('/',404)
        