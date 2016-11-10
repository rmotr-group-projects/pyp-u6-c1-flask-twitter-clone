import sqlite3
from hashlib import md5
from functools import wraps
from flask import Flask
from flask import (g, request, session, redirect, render_template,
                   flash, url_for)

app = Flask(__name__)
DATABASE_NAME = 'twitter.db'

def connect_db(db_name):
    return sqlite3.connect(DATABASE_NAME)

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


def md5_hash(mhash):
    if mhash != None:
        hash_object = md5(mhash)
        return hash_object.hexdigest()
    else:
        return "1234-error-password"


@app.route('/', methods=["POST", "GET"])
@login_required
def index():
    user_id = g.db.execute('SELECT id FROM user WHERE username = ?', (session['username'],))
    user = user_id.fetchone()[0]
    if request.method == "POST":
        tweet = str(request.form['tweet'])
        
        if len(tweet) <= 140:
            cursor = g.db.execute('INSERT INTO tweet ("user_id", "content") VALUES (?, ?);', (user, str(tweet),))
            g.db.commit()
            flash('Tweet successfully posted', 'success')
            return redirect(url_for('index'))
        else:
            flash('Maximum Tweet Character Length Exceeded')
            return redirect(url_for('index'))
        
        if request.form['delete_tweet'] == 'Delete':
            print("deleted")
    
    if request.method == "GET":
        user_id = g.db.execute('SELECT id FROM user WHERE username=?',(session['username'],))
        uid = user_id.fetchone()
        content = g.db.execute('SELECT * FROM tweet WHERE user_id=?',(uid[0],))
        tweets = content.fetchall()
        return render_template('static_templates/own_feed.html', user=session['username'], tweets=reversed(tweets))


@app.route('/<user>', methods=["POST", "GET"])
def user_page(user):
    """
    Gets the user, compiles their username and tweet info, posts it
    """
    id_cursor = g.db.execute('SELECT id FROM user WHERE username=?',(user,))
    try:
        user_id = id_cursor.fetchone()[0]
    except:
        user_id = None
    tweets_cursor = g.db.execute('SELECT * from tweet WHERE user_id=?',(user_id,))
    tweets = tweets_cursor.fetchall()
    print(tweets)
    if user_id != None:
        return render_template('static_templates/other_feed.html', user=session['username'], tweets=reversed(tweets))
    if user_id == None:
        flash('Account Not Found')
        return redirect('/')


@app.route('/search', methods=["POST", "GET"])
def search():
    if request.args.get('search_user'):
        return redirect('/{}'.format(request.args.get('search_user')))
    else:
        return redirect('/')


@app.route('/delete_tweet/<id>', methods=["POST"])
@login_required
def delete_tweet(id):
    if request.method == "POST":
        user_id = g.db.execute('SELECT id FROM user WHERE username = ?', (session['username'],))
        user = user_id.fetchone()[0]
        tweets = g.db.execute('DELETE FROM tweet WHERE user_id=? AND id=?', (user,id,))
        g.db.commit()
        flash("Tweet Successfully Deleted", "success")
        return redirect(url_for('index'))


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = md5_hash(request.form['password'])
        cursor = g.db.execute("SELECT * FROM user WHERE username=? and password=?;", (username, password,))
        account = cursor.fetchone()
        
        if account != None:
            session['username'] = username
            return redirect('/')
        
        if account == None:
            flash('Invalid password, please try again!')
            return redirect(url_for('login'))
        
    if request.method == 'GET':
        return render_template('static_templates/login.html')


@app.route('/profile', methods=["POST", "GET"])
@login_required
def profile():
    if request.method == 'GET':
        cursor = g.db.execute('SELECT * FROM user WHERE username=?',(session['username'],))
        user_info = cursor.fetchone()
        return render_template('static_templates/profile.html', user=session['username'], user_info=user_info)


@app.route('/update', methods=["POST", "GET"])
@login_required
def update():
    if request.method == "POST":
        user_id = g.db.execute('SELECT id FROM user WHERE username = ?', (session['username'],))
        user = user_id.fetchone()[0]
        
        if request.form['first_name']:
            g.db.execute('UPDATE user SET first_name=? WHERE id=?', (request.form['first_name'], user,))
            
        if request.form['last_name']:
            g.db.execute('UPDATE user SET last_name=? WHERE id=?', (request.form['last_name'], user,))
            
        if request.form['birth_date']:
            g.db.execute('UPDATE user SET birth_date=? WHERE id=?', (request.form['birth_date'], user,))
        
        g.db.commit()
        flash('Your profile was correctly updated')
        return redirect('/profile')


@app.route('/logout')
@login_required
def logout():
    flash('Successfully Logged Out')
    session.pop('username', None)
    return redirect('/')
