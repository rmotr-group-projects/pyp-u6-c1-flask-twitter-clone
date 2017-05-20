import sqlite3, datetime
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
            return redirect(url_for('login', next=request.url), 302)
        return f(*args, **kwargs)
    return decorated_function



@app.route('/login', methods=['GET', 'POST'])
def login():
    '''
    This function serves the login page to the user on 'GET', and it authenticates the user on 'POST'
    Flashes login error at the top of login template upon authentication failure
    '''
    
    #create local var to indicate the next routing destination 
    # -- root route is default 
    # -- param 'next' can be passed in from a login_required decorated route function's redirect() return value
    next = request.args.get('next', '/')
    if request.method == 'POST':
        session['username'] = request.form['username']
        password = md5(request.form['password'].encode('utf-8')).hexdigest()
        
        #fetch password from a record (tuple) of given username --note that execute() accepts var substitutions from a List of vars
        cursor = g.db.cursor()
        cursor.execute('SELECT password, id FROM user WHERE username=?', [session['username']])
        
        record = cursor.fetchone()

        #Authenticate iff a record has been found in the db and the passwords match
        if record is not None:
            if record[0] == password:
                session['user_id'] = record[1] #save user(id) to session for future access
                return redirect(next)
            else:
                session.pop('username', None) # IMPORTANT! Refresh current session!
                flash("Invalid username or password.")
                return render_template('login.html')
        else:
            flash("Invalid username or password.")
            return render_template('login.html')
           
    #serve up login page 
    if request.method == 'GET':
        if 'username' in session: return redirect(next);
        
        else: return render_template('login.html');



@app.route('/logout', methods=['GET'])
def logout():
    '''
    This function resets the user's currently active session
    '''
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect('/', 302)



@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    '''
    This function serves up the  VIEW user's personal profile if a session exists.
    'POST' allows the user to submit changes to their profile and commits the changes to the db.
    
    Flashes success message when db is successfully updated, and failure when date string is not a valid date
    '''
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        birth_date = request.form['birth_date']
        
        #confirm valid date string and commit subsequent update to db
        try:
            datetime.datetime.strptime(birth_date, '%Y-%m-%d')
            cursor = g.db.cursor()
            cursor.execute('UPDATE user SET first_name=?, last_name=?, birth_date=? WHERE username=?', [first_name, last_name, birth_date, session['username']])
            g.db.commit()
            flash("Your profile has been updated.")
        except:
            flash("Invalid date. Please enter a valid date with format 'YYYY-MM-DD'.")

        
        info = {'first_name':first_name, 'last_name':last_name, 'birth_date':birth_date, 'usr':session['username']}
        return render_template('static_templates/profile.html', **info)
        
        
    
    if request.method == 'GET':
        cursor = g.db.cursor()
        cursor.execute('SELECT first_name, last_name, birth_date, username FROM user WHERE username=?', [session['username']])
        
        record = cursor.fetchone()
        
        info = {'first_name':record[0], 'last_name':record[1], 'birth_date':record[2], 'usr':record[3]}
        return render_template('static_templates/profile.html', **info)
        



def other_feed(uid, usr):
    '''
    This function serves up the VIEW 'other_feed.html' template 
    
    TODO: dynamically generate html pages of tweets pulled from db upon request
    '''
    if request.method == 'GET':
        
        tweets = gen_feed(uid, usr)
        tweets['username'] = usr
        flash(tweets)
        return render_template('static_templates/other_feed.html', **tweets)
    


@app.route('/tweets/<some_id>/delete', methods=['GET','POST'])
@login_required
def delete_tweet(some_id):
    '''
    This function alters the MODEL of a user's tweet TABLE in the db.
    It will delete the desired tweet (informed by the POST request sent by clicking a given delete button)
    '''
    next = request.args.get('next', '/')
    if request.method == 'POST':
        if not some_id.isdigit():
            return render_template(next), 404
        cursor = g.db.cursor()
        cursor.execute('DELETE FROM tweet WHERE id=?', [some_id])
        g.db.commit()
        
        tweets = gen_feed(uid=session['user_id'], usr=session['username'])
            
        return redirect(next)
        
    if request.method == 'GET':
        return render_template(next), 404
  

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    '''
    This function directs to the user's (authenticated) homepage
    '''
    return homepage()
    
    
    
@app.route('/<usr>', methods=['GET', 'POST'])
def process_usr_request(usr):
    '''
    This function CONTROLS the page of a specified user. 
    If the desired 'usr' is the currently logged in user, serve up the homepage slash 'own_feed' template
    '''
    if 'username' in session:
        if usr == session['username']:
             return homepage()
         
    cursor = g.db.cursor()
        
    cursor.execute('SELECT id FROM user WHERE username=?', [usr])
    
    choice = cursor.fetchone()
    
    if choice is not None:
        return other_feed(choice[0], usr)
        
    return redirect(url_for('login'), 404)

   
   

@login_required
def homepage():
    '''
    This function serves up the VIEW of the user's personal feed if an authenticated session exists.
    'POST' allows the user to submit new tweets they wish to publish to their feed.
    '''
    if request.method == 'POST':
        submit_tweet()
        
        tweets = gen_feed(uid=session['user_id'], usr=session['username'])
        
        return render_template('own_feed.html', **tweets)
    
    if request.method == 'GET':
        
        tweets = gen_feed(uid=session['user_id'], usr=session['username'])

        flash(tweets)
        return render_template('own_feed.html', **tweets)
    
@login_required
def submit_tweet():
    '''
    This function alters the MODEL of the user's homepage. 
    It retrieves the contents of a tweet submitted by the user and creates an entry in the user's tweet table
    '''
    cursor = g.db.cursor()
    tweet = request.form['tweet']
        
    cursor.execute('INSERT INTO tweet (user_id, content) VALUES (?, ?)', [session['user_id'], tweet])
    g.db.commit()
    

def gen_feed(uid, usr):
    '''
    This function  generates the MODEL of all tweets that are to be displayed on a tweet feed
    '''
    cursor = g.db.cursor()
    cursor.execute('SELECT * FROM tweet WHERE user_id=?', [uid])
        
    columns = [column[0] for column in cursor.description]
    tweets = {}
    tweets['rows'] = []
    for row in cursor.fetchall():
        tweets['rows'].append(dict(zip(columns, row)))
    tweets['username'] = usr
            
    return tweets
    
    