import sqlite3
# import settings
from hashlib import md5
from functools import wraps
from flask import Flask

from flask import (g, request, session, redirect, render_template,
                   flash, url_for, make_response)

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



@app.route('/', methods=['POST', 'GET'])
@login_required
# show feed at the root url if already logged in.
def home():
    if request.method == 'GET':
        return(feed(username=session.get('username','')))
    if request.method == 'POST':
        # We need to call the feed method and pass it the request object
        return(feed(username=session.get('username',''), forwarded_request=request))

@app.route('/login', methods=['POST', 'GET'])
def login():
    if session.get('username','') != '':
        return redirect(url_for('home'))
    if request.method == 'GET':
        next_url = request.args.get('next', '')
        if next_url != '':
            session['next'] = next_url
        return render_template('login.html')
    elif request.method == 'POST':
        #Check user credentials
        submitted_username = request.form['username'].strip()
        submitted_password = request.form['password'].strip()
        if len(submitted_username) == 0:
            return "Login failed - username cannot be blank"
        if len(submitted_password) == 0:
            return "Login failed - password cannot be blank"
        hashed_password = md5(submitted_password.encode(request.charset)).hexdigest()
        sql_string = '''
            SELECT * from user;
        '''
        cursor = g.db.execute(sql_string)
        fields = cursor.fetchall() 
        if len(fields) == 0:
            return "No registered users - can't authenticate"
        
        for field in fields:
            if field[1] == submitted_username:
                #check password
                if field[2] == hashed_password:
                    # Succesful authentication: keep a record of this
                    session['username'] = submitted_username
                    session['user_id'] = field[0]
                    # Check to see if we have a next page to go to, otherwise
                    # Default to feed
                    tmp_next = session.get('next','')
                    if tmp_next != '':
                        session.pop('next')
                        return redirect(tmp_next)
                    return redirect(url_for('feed', username=session['username']))
        return "Invalid username or password"
        
@app.route('/<username>', methods=['POST', 'GET'])
def feed(username, forwarded_request = None):
    
    if request.method == 'GET':
        tweets = get_tweets(username)
        return render_template('feed.html', tweets=tweets, logged_in=session.get('username',''), username=username)
                    
    if request.method == 'POST':
        # only logged in users can post
        if 'username' not in session:
            return make_response("You cannot tweet if you are not logged in", 403) 
        if forwarded_request != None:
            # We have been forwarded a request object. Use this instead of the normal one.
            myrequest = forwarded_request
        else:
            myrequest = request
            
        submitted_tweet = myrequest.form['tweet'].strip()
        if submitted_tweet != '':
            # We will insert a new tweet into the tweet table
            sql_string = '''
                INSERT INTO tweet
                (
                    user_id, content
                )
                VALUES
                (
                    (
                        SELECT id from user
                        WHERE username = '{}'
                    ),
                    '{}' 
                );
            '''
            sql_string = sql_string.format(session['username'], submitted_tweet)
            cursor = g.db.execute(sql_string) 
            g.db.commit()
            # Now, lets return the refreshed feed:
            tweets = get_tweets(username)
            return render_template('feed.html', tweets=tweets, logged_in=session.get('username',''), username=username)
            
def get_tweets(username):
    sql_string = '''
        SELECT
        tweet.id, tweet.created, tweet.content, user.username
        FROM
        tweet, user
        WHERE
        user.username = '{}'
        AND
        user.id = tweet.user_id
        ORDER BY
        tweet.created DESC
    '''
    sql_string = sql_string.format(username)
    cursor = g.db.execute(sql_string)
    results = cursor.fetchall()
    tweets = [{'id':result[0], 'created':result[1], 'content':result[2] } for result in results]
    return tweets

@app.route('/tweets/<int:tweet_id>/delete', methods=['POST', 'GET'])
@login_required      
def delete_tweet(tweet_id):
        sql_string = '''
            DELETE
            FROM
            tweet
            WHERE
            tweet.id = {}
        '''
        sql_string = sql_string.format(tweet_id)
        g.db.execute(sql_string)
        g.db.commit()
        
        # OK, now back to the home page
        return redirect(url_for('home'))
        
@app.route('/profile', methods=['POST', 'GET'])
@login_required      
def profile():
    
    if request.method == 'GET' :
        profile_data = get_profile_data(session['username'])     
        status = request.args.get('status', '')
        return render_template(
            'profile.html',
            profile_data=profile_data,
            username=session['username'],
            status=None,
            logged_in=session['username']
        )
                    
    if request.method == 'POST':
        # Process the posted data
        submitted_first_name = request.form['first_name'].strip()
        submitted_last_name = request.form['last_name'].strip()
        submitted_birth_date = request.form['birth_date'].strip()
        
        sql_string = '''
            UPDATE
            user
            SET
            first_name = '{}',
            last_name = '{}',
            birth_date = '{}'
            WHERE
            username = '{}'
        '''
        sql_string = sql_string.format(
            submitted_first_name,
            submitted_last_name,
            submitted_birth_date,
            session['username']
        ) 
        
        try:
            g.db.execute(sql_string)
            g.db.commit()
            status = 'success'
        except:
            status = 'failure'
        
        profile_data = get_profile_data(session['username'])     
        return render_template(
            'profile.html',
            profile_data=profile_data,
            username=session['username'],
            status=status,
            logged_in=session['username']
        )

def get_profile_data(username):
    sql_string = '''
            SELECT
            first_name, last_name, birth_date
            FROM
            USER
            WHERE
            username = '{}'
        '''
    sql_string = sql_string.format(session['username'])
    cursor = g.db.execute(sql_string)
    results = cursor.fetchall() 
    profile_data = {'first_name':results[0][0], 'last_name':results[0][1], 'birth_date':results[0][2]}
    return profile_data
        
        
@app.route('/logout', methods=['GET'])
def logout():
    if "username" in session:
        session.pop('username')
        session.pop('user_id')
        return redirect(url_for('home'))
        
    if 'username' not in session:
        return ("You are not logged in. Cannot log out.")
        
app.secret_key = 'V\xf1\xfd\x92\x98\xb3\xe1\x80{0\x91\x9amy\x8f#U\x1e\x12_\xf4\xc8\xf9b'