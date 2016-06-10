import sqlite3
from hashlib import md5
from functools import wraps
from flask import Flask
from flask import (g, request, session, redirect, render_template,
                   flash, url_for, abort)
import datetime

app = Flask(__name__)

DANGER = 'danger'
SUCCESS = 'success'

def connect_db(db_name):
    return sqlite3.connect(db_name)


def _hash_password(password):
    '''
    Returns the MD5 hash of the user's entered password
    '''
    # password_bytes = str.encode(password)
    password_bytes = password.encode('utf-8')
    return md5(password_bytes).hexdigest()


def _date_check(date):
    '''
    Check for date format accuracy
    '''
    try:
        return datetime.datetime.strptime(date, '%Y-%m-%d')
    except:
        return False


def _valid_tweet(tweet):
    '''
    Validate the entered tweet data
    '''
    return 0 < len(tweet) and len(tweet) <= 140


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
def base():
    '''
    Redirect user to login page.
    '''
    
    # If not logged in, redirect to login page
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    # If logged in, redirect to feed page
    else:
        return redirect(url_for('feed', username=session['username']))


@app.route('/login', methods=['GET', 'POST'])
def login():
    '''
    Present user to login page redirect to feed if already logged in
    '''
    
    # If logged in already, redirect to the user feed
    if 'logged_in' in session:
        return redirect(url_for('base'))
    
    # If not logged in, on GET request render the blank login template
    if request.method == 'GET':
        return render_template('login.html')
    
    # On POST request validate user data and initiate session or display error
    else:

        user_pass = _hash_password(request.form['password'])
        username = request.form['username']
        # registered_user = False
        
        # Verify that the username matches a registered user
        # query = 'SELECT id FROM user WHERE username=?'
        # try:
        #     cursor = g.db.execute(query, (username,))
        #     results = cursor.fetchall()
        #     assert results
        #     registered_user = True
        # except:
        #     flash('Invalid username')
        #     flash_type = DANGER
        
        # # If the user is registered, verify that the password is correct
        # if registered_user:
        #     query = 'SELECT id FROM user WHERE username=? AND password=?'
        #     try:
        #         cursor = g.db.execute(query, (username,user_pass))
        #         results = cursor.fetchall()
        #         assert results
        #         session['user_id'] = results[0][0]
        #     except:
        #         flash('Invalid password')
        #         flash_type = DANGER
        
        # Validate the username and password
        query = 'SELECT id FROM user WHERE username=? AND password=?'
        try:
            cursor = g.db.execute(query, (username,user_pass))
            results = cursor.fetchall()
            assert results
            session['user_id'] = results[0][0]
        except:
            flash('Invalid username or password')
            flash_type = DANGER
        
        # Initiate the session and redirect to the user feed
        if 'user_id' in session:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('base'))
        
        # Display an error and remain on login page
        return render_template('login.html', flash_type=flash_type)


@app.route('/logout')
def logout():
    '''
    Log out the user and redirect to the login page.
    Alternatively, could redirect to the frontpage (user feed)
    '''
    session.clear()
    flash('You were logged out')
    return redirect(url_for('base'))
    
    
@app.route('/<username>', methods=['GET', 'POST'])
def feed(username):
    
    # Set a default flash type.  This will be used if redirected here
    #  from an invalid delete and will be overwritten if a tweet is
    #  posted successfully.
    flash_type = DANGER
    
    # Verify that the user exists, and get the user's id
    query = 'SELECT id FROM user WHERE username=?'
    try:
        cursor = g.db.execute(query, (username,))
        results = cursor.fetchall()
        assert results
    except:
        abort(404) # TODO: Customize this?
    
    u_id = results[0][0]
    
    # Is the user logged in and viewing their own page?
    own = 'logged_in' in session and u_id == session['user_id']
    
    # If the user is posting a tweet, validate it and add it.
    if request.method == 'POST':
        tweet = request.form['tweet']
        if not own:
            # flash('You may not tweet from this account')
            abort(403)
        elif not _valid_tweet(tweet):
            flash('Your tweet was either too short or too long')
        else:
            # Add the tweet to the database
            query = '''INSERT INTO "tweet" ("user_id", "content")
                VALUES (?, ?);'''
            g.db.execute(query, (u_id, tweet))
            g.db.commit()
            flash('Tweet posted successfully')
            flash_type = SUCCESS
            
    # Get all tweet data for this user
    query = '''SELECT u.username, t.id, t.created, t.content, u.id 
        FROM user as u INNER JOIN tweet as t
        ON u.id=t.user_id
        WHERE u.username=?
        ORDER BY t.created DESC;'''
    cursor = g.db.execute(query, (username,))
    tweets = cursor.fetchall()
    
    # Display the user's twitter feed page
    return render_template('feed.html', own=own, tweets=tweets, flash_type=flash_type)

@app.route('/tweets/<t_id>/delete', methods=['POST'])
# @login_required  # Replaced by code on lines 223 - 225
def delete(t_id):
    
    # Get information about the tweet to be deleted
    query = '''SELECT t.user_id, u.username
        FROM tweet AS t INNER JOIN user AS u 
        ON t.user_id=u.id
        WHERE t.id=?;'''
    
    # If the tweet id given is not valid or no such tweet exists, return a 404
    try:
        cursor = g.db.execute(query, (t_id,))
        results = cursor.fetchall()
        assert results
    except:
        abort(404) # TODO: Customize this?
    
    # Verify that the user deleting a tweet is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Determine whose tweet is being deleted
    u_id = results[0][0]
    username = results[0][1]
    
    # Verify that the authenticated user is deleting his own tweet
    if u_id != session['user_id']:
        flash('''You can't just go around deleting other people's tweets!
            How would you feel if someone deleted one of your tweets?''')
    
    # Delete the tweet
    else:
        query = '''DELETE FROM tweet WHERE id=?;'''
        g.db.execute(query, (int(t_id),))
        g.db.commit()
        
    # Redirect to the user's feed
    # return redirect(url_for('feed', username=username))
    return redirect(url_for('base'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    '''
    Obtain the user details and pass to the profile templage for reply.
    '''
    error = None 
    flash_type = SUCCESS
    # return render_template('login.html')
    query = '''SELECT username, first_name, last_name, birth_date 
        FROM user
        WHERE id=?;'''
    cursor = g.db.execute(query, (str(session['user_id']),))
    results = cursor.fetchone()
    (user, fn, ln, dob) = results

    if request.method == 'POST':

        # If the user supplies an invalid date, error out and don't save
        if request.form['birth_date'] and not _date_check(request.form['birth_date']):
            flash('Invalid date')
            flash_type = DANGER
            
        # If the user supplies no date or a valid date, save the updates
        else:
            query = '''UPDATE user 
                SET first_name=?, last_name=?, birth_date=? 
                WHERE id=?;'''
            fn = request.form['first_name'] or fn
            ln = request.form['last_name'] or ln
            dob = request.form['birth_date'] or dob
            g.db.execute(query, (fn, ln, dob, str(session['user_id'])))
            g.db.commit()
            
            flash('Updated')

    return render_template('profile.html', user=user, fname=fn, lname=ln, dob=dob, flash_type=flash_type)

@app.route('/register', methods=['GET', 'POST'])
def register():
    '''
    Register a new user, validate registration information, and store user in
    database.
    '''
    
    # If a user is logged in, return to the base page
    if 'logged_in' in session:
        return redirect(url_for('base'))
    
    # Display messages for possible entry and validation errors
    UN_ERROR = 'The username you chose has already been registered.  \
        Please select a different username.'
    PW_ERROR = 'The passwords entered do not match each other.'
    DOB_ERROR = 'The date of birth you entered is in an invalid format.  \
        Please enter your date of birth in the form "YYYY-MM-DD".'
    
    # Use placeholder values in the registration template
    if request.method == 'GET':
        user = fname = lname = dob = ''
    
    # Validate entered data.  If validation passes, store the new user and
    #  redirect to the login screen.  If it fails, remain on the registration
    #  page, with any valid values still in the form.
    if request.method == 'POST':
        valid = True
        
        # See if the username has been used already
        query = 'SELECT * FROM user WHERE username=?;'
        cursor = g.db.execute(query, (request.form['username'],))
        results = cursor.fetchall()
        if results:
            valid = False
            flash(UN_ERROR)
            user = ''
        else:
            user = request.form['username']
        
        # Validate the password
        if request.form['password1'] != request.form['password2']:
            valid = False
            flash(PW_ERROR)
        pw = _hash_password(request.form['password1'])
        
        # Validate the birthdate format
        if request.form['birth_date'] and not _date_check(request.form['birth_date']):
            valid = False
            flash(DOB_ERROR)
            dob = ''
        else:
            dob = request.form['birth_date']
        
        # Get names out of the form
        fname = request.form['first_name']
        lname = request.form['last_name']
        
        # If validation passes, store the new user and go to the login page
        if valid:
            
            # Store user data in database
            query = '''INSERT INTO user 
                (username, password, first_name, last_name'''
            if dob:
                query += ', birth_date) VALUES (?, ?, ?, ?, ?);'
                user_data = (user, pw, fname, lname, dob)
            else:
                query += ') VALUES (?, ?, ?, ?);'
                user_data = (user, pw, fname, lname)
            g.db.execute(query, user_data)
            g.db.commit()
            
            # Send the user to the login page
            return redirect(url_for('login'))
            
    # Remain on the register page
    return render_template(
        'register.html',
        user=user,
        fname=fname,
        lname=lname,
        dob=dob,
        flash_type=DANGER
    )