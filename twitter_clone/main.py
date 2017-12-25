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

@app.route('/login', methods=['GET', 'POST'])
def login():
    next = request.args.get('next', '/')

    if 'username' in session:
        return redirect(next)

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor = g.db.execute(
            'SELECT id, password FROM user WHERE username=:username;',
            {'username': username})
        user = cursor.fetchone()
        hashed_pwd = md5(password.encode('utf-8')).hexdigest()
        
        if user and user[1] == hashed_pwd:
            session['user_id'] = user[0]
            session['username'] = username
            flash('You were correctly logged in', 'success')
            return redirect(next)

        flash('Invalid username or password', 'danger')

    return render_template('login.html', next=next)

@app.route('/logout')
@login_required
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect('/')

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
            'first_name': request.form.get('first_name'),
            'last_name': request.form.get('last_name'),
            'birth_date': request.form.get('birth_date'),
            'username': session['username']
        }
        g.db.execute('UPDATE user SET first_name = :first_name, last_name = :last_name, birth_date = date(:birth_date) WHERE id = :id;', params)
        g.db.commit()

    return render_template('static_templates/profile.html')

@app.route('/<username>', methods=['GET', 'POST'])
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
def tweet(tweet_id):
    params = {'id' : tweet_id }
    
    cursor = g.db.execute('SELECT * FROM tweet WHERE id = :id;', params)
    tweet = cursor.fetchone()
    if not tweet:
        abort(404)
    
    g.db.execute('DELETE FROM tweet WHERE id = :id;', params)
    g.db.commit()
    return redirect('/')


@app.route('/', methods=['GET'])
@login_required
def index():
    if 'username' in session:
        return redirect('/{}'.format(session['username']))