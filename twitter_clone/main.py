import sqlite3
from hashlib import md5
from functools import wraps
from flask import Flask
from flask import (g, request, session, redirect, render_template,
                   flash, url_for,abort)

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
def landing():
    if 'username' not in session:
        return redirect(url_for('login'))
    else:
        return render_template('static_templates/own_feed.html')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    url_redirect = request.args.get('next','/')
    
    if 'username' in session:
        return redirect(url_redirect)
        
    if request.method == 'POST':
        
        password = request.form['password']
        username = request.form['username']
        pwhash = md5(password.encode('utf-8')).hexdigest()
        
        #get user data from DB
        sql_query="select id, password from user where username = :username;"
        cursor = g.db.execute( sql_query, {'username': username})
        # [[user, password], [user,password]]
        db_users = cursor.fetchone()
        #authenticate
        if db_users is not None and pwhash == db_users[1]:
            session['user_id'] = db_users[0]
            session['username'] = username
            return redirect(url_redirect)
        return('Invalid username or password')

    return render_template('static_templates/login.html', next = url_redirect)

@app.route('/profile', methods = ['POST', 'GET'])
@login_required
def edit_profile():
    if request.method == 'POST':
        sql_query = "UPDATE user SET first_name = :first_name, last_name = :last_name, birth_date = :birth_date where id = :user_id;"
        params = {'user_id': session['user_id'], 'first_name': request.form['first_name'],
                'last_name': request.form['last_name'], 'birth_date': request.form['birth_date']}
        cursor = g.db.execute(sql_query, params)
        g.db.commit()
    return render_template('dynamic_templates/profile.html')


@app.route('/<username>', methods = ['POST', 'GET'])
def view_feed(username):
    
    allow_insert = False
    if 'username' in session and session['username'] == username:
        # if session['username'] == username:
        allow_insert = True      
    elif request.method == 'POST' and 'username' not in session:
        return redirect('/login'), 403
    
    if request.method == 'POST' and allow_insert:
        tweet = request.form['tweet']
        sql_query='''
                INSERT INTO "tweet" ("user_id", "content") 
                VALUES (:sessionid, :content);
                '''
        cursor = g.db.execute(sql_query, {'sessionid': session['user_id'],'content':tweet})
        g.db.commit()
    
    #get user's feed from DB
    sql_query='''
                select b.id, b.created, b.content 
                from user a inner join tweet b on a.id = b.user_id
                where a.username = :username;
                '''
    cursor = g.db.execute( sql_query, {'username': username})
    tweets = [dict(id = row[0], created = row[1], content = row[2])
                for row in cursor.fetchall()]
    
    return render_template('dynamic_templates/feed.html', username = username, tweets = tweets, doinsert = allow_insert)
    
'''  
@app.route('/<username>')
def view_feed(username):
    
    if 'username' in session:
        if session['username'] == username:
            return redirect(url_for('insert_feed'), code = 200)
    
    #get user's feed from DB
    sql_query=''-
                select b.created, b.content 
                from user a inner join tweet b on a.id = b.user_id
                where a.username = :username;
                -''
    cursor = g.db.execute( sql_query, {'username': username})
    tweets = [dict(created = row[0], content = row[1])
                for row in cursor.fetchall()]
        
    return render_template('dynamic_templates/other_feed.html', username = username, tweets = tweets)

@app.route('/feed', methods = ['GET','POST'])
@login_required
def insert_feed():
    print('==================')
    my_username = session['username']
    print('{} already login'.format(my_username))
    if request.methods == 'POST':
        #do db insert
        return redirect('/{}'.my_username)
    
    sql_query=''-
                select b.id , b.created, b.content 
                from user a inner join tweet b on a.id = b.user_id
                where a.username = :username;
                -''
    cursor = g.db.execute( sql_query, {'username': my_username})
    tweets = [dict(id = row[0], created = row[1], content = row[2])
                for row in cursor.fetchall()]
    print('returning own_feed')  
    return render_template('dynamic_templates/own_feed.html', username = my_username, tweets = tweets)
'''

@app.route('/tweets/<tweet_id>/delete', methods = ['POST'])
def deletetweet(tweet_id):
    url_redirect = request.args.get('next','/')
    check_if_tweet_exists = "Select * from tweet where id = :tweet_id;"
    params = {"tweet_id":tweet_id}
    cursor = g.db.execute(check_if_tweet_exists, params)
    if not cursor.fetchone():
        # is it getting into here?
        #
        return render_template('/static_templates/own_feed.html'), 404
    if 'username' not in session:
        return redirect('/login')
    sql_query = "DELETE from tweet where id = :tweet_id and user_id = :user_id;"
    params2 = {"user_id":session['user_id'], "tweet_id":tweet_id}
    g.db.execute(sql_query, params2)
    g.db.commit()
    return redirect(url_redirect)
        
@app.route('/logout')
@login_required
def logout():
    next_url = request.args.get('next', '/')
    session.pop('user_id')
    session.pop('username')
    return redirect(next_url)