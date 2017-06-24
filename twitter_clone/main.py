import sqlite3
from hashlib import md5
from functools import wraps
from flask import Flask
from flask import (g, request, session, redirect, render_template,
                   flash, url_for, abort)
import datetime as datetime

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
def home():
    if 'username' in session:
        return redirect('/{}'.format(session['username']))
    

@app.route('/login', methods=['GET', 'POST'])
def login():
    next = request.args.get('next', '/')
    
    if request.method == 'POST':
        username = request.form['username']
        hash_password = md5(request.form['password'].encode('utf-8')).hexdigest()
        
        cursor = g.db.execute('SELECT id, password FROM user WHERE username=:username;',{'username': username})
        user = cursor.fetchone()
        
        if user and user[1] == hash_password:
            session['user_id'] = user[0]
            session['username'] = username
            session['password'] = hash_password
            return redirect(next)
        else:
            return("Invalid username or password.",200)
            
    if request.method == 'GET':
        if 'username' in session:
            return redirect(next)
        else:
            return render_template('static_templates/login.html', next=next)
        
        
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect('/')


@app.route('/<username>', methods=['GET', 'POST'])
#@login_required
def user_info(username):
    
    
    if request.method == 'POST':
        
        if username == session.get('username', None):
            new_tweet = request.form['tweet']
            cursor = g.db.execute('SELECT id FROM user where username=:username', {'username': username})
            user_id = cursor.fetchone()[0]
            g.db.execute('INSERT INTO tweet (user_id, content) VALUES (:user_id, :content)', {'user_id': user_id, 'content': new_tweet})
            g.db.commit()
        else:
            return 'User not authenticated', 403

    
    cursor = g.db.execute('SELECT u.username, t.id, t.created, t.content FROM user u, tweet t where u.id = t.user_id and u.username=:username', {'username': username})
    tweets = []
    for r in cursor.fetchall():
        tweets.append({'username': r[0], 'id': r[1], 'created': r[2], 'content': r[3]})
        #print('{} {}'.format(r[0],r[1]))
    
    #print tweets
    #for t in tweets:
    #    print t['content']
    
    if username == session.get('username', None):
        return render_template('static_templates/own_feed.html',username=username, tweets=tweets)
    else:
        return render_template('static_templates/other_feed.html',username='', tweets=tweets)
        

@app.route('/profile', methods=['GET', 'POST'])   
@login_required   
def get_profile():

    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        birth_date = request.form['birth_date']
        
        try:
            datetime.datetime.strptime(birth_date, '%Y-%m-%d')
            cursor = g.db.cursor()
            cursor.execute('UPDATE user SET first_name=?, last_name=?, birth_date=? WHERE username=?', [first_name, last_name, birth_date, session['username']])
            g.db.commit()
            return("Your profile has been updated")
        except:
            return("Invalid date. Please enter a valid date with format 'YYY-MM-DD'.")
            
    username = session['username']
    cursor = g.db.execute('SELECT id, first_name, last_name, birth_date FROM user WHERE username=:username', {'username': username})
    res = cursor.fetchone()
    id, first_name, last_name, birth_date = res
    return render_template('static_templates/profile.html', username=username, first_name=first_name, last_name=last_name, birth_date=birth_date )

@app.route('/tweets/<tweet_id>/delete', methods=['POST'])
#@login_required
def delete_tweet(tweet_id):

    #if not isinstance(tweet_id, int) #and 'username' not in session:
    #   return 'Invalid tweet id {}'.format(tweet_id), 404

#    if 'username' not in session:
#        if not isinstance(tweet_id, unicode):
#             return 'Invalid tweet id {}'.format(tweet_id), 404
#        return redirect('/login')
    
    #cursor = g.db.execute('SELECT u.username, t.user_id FROM user u, tweet t WHERE u.id = t.user_id and u.username=:username and t.id=:id', #{'username': session.get('username',None),'id': tweet_id})
    #cursor = g.db.execute('SELECT u.username, t.user_id FROM user u, tweet t WHERE u.id = t.user_id and u.username=:username and t.id=:id', #{'username': session.get('username',None),'id': tweet_id})
    cursor = g.db.execute('SELECT user_id FROM tweet WHERE id=:id', {'id':tweet_id})
    result = cursor.fetchone()
    print (result)
    if result is None:
        return 'Invalid tweet id {}'.format(tweet_id), 404
    else:      
        #tweet_username, user_id = result
        if result[0] == session.get('user_id', None):
            cursor = g.db.execute('DELETE FROM tweet WHERE id=:id', {'id': tweet_id})
            g.db.commit()
            return redirect('/')
        else:
            return redirect('/login')

            

    
    

