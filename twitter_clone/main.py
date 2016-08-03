import sqlite3
from hashlib import md5
from functools import wraps
from flask import Flask
from flask import (g, request, session, redirect, render_template,
                   flash, url_for)
import re


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



# Index view
@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('feed', username=session['username'])) #'/{}'.format(session['username']))
    return redirect(url_for('login'))

'''
Basic Render_Template template
@app.route('/hello/')
@app.route('/hello/<name>')
def hello(name=None):
    return render_template('hello.html', name=name)
'''

# login view
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = hash_function(request.form['password'])

        # query = 'SELECT username, password FROM user '#WHERE username=:username;'
        # subs = {'username': username}
        # cursor = g.db.execute(query)
        # users = cursor.fetchall()
        
        users = basic_query('user', 'username, password')

        
        for user in users:
            if user[0] == username and user[1] == password:
                session['username'] = username
                flash('You were logged in')
                return redirect(url_for('index'))
        error = 'Invalid password or username.'
            
    return render_template('login.html', error=error)
    
    
# profile view
# profile = app.route(blah)(login_required(profile))
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    
    if request.method == 'POST':
        form = request.form
        print(form['birth_date']) #2016-01-26
        print(session['username'])
        print(form) #ImmutableMultiDict([('username', u'martinzugnoni'), ('birth_date', u'2016-01-26'), ('first_name', u'MArtin'), ('last_name', u'BLah')])
        query = 'UPDATE user SET first_name = {first_name}, last_name = {last_name}, birth_date = \
        {birth_date} WHERE username = {username}'.format(first_name=form['first_name'], last_name=form['last_name'], \
        birth_date=form['birth_date'], username=session['username'])
        g.db.execute(query)
        
    
    user_data = {}
    users = basic_query('user', 'username, first_name, last_name, birth_date')
    for user in users:
        if session['username'] == user[0]:
            user_data = {'username':user[0], 'first_name':user[1], 'last_name':user[2], 'birth_date':user[3]}
             
    return render_template('profile.html', user=user_data)




# feed view
@app.route('/<username>', methods=['GET', 'POST'])
def feed(username):
    
    # Gets user Tweets
    user_id = None
    users = basic_query('user', 'username, id')
    for user in users:
        if username == user[0]:
             user_id = user[1]

    all_tweets = basic_query('tweet', 'user_id, created, content') 
    user_tweets = []
    for tweet in all_tweets:
        if user_id == tweet[0]:
            user_tweets.append({'created':tweet[1], 'content':tweet[2]})

    # User Tweeting
    if request.method == 'POST':
        tweet_text = request.form['tweet']
        basic_insert('tweet', ("user_id", "content"), tweet_text)
        pass
            
    if 'username' in session and session['username'] == username:
        return render_template('own_feed.html', username=session['username'], tweets=user_tweets)
    else:
        return render_template('other_feed.html', username=session['username'], tweet_user=username, tweets=user_tweets)


@app.route('/logout')
def logout(next=None):
    session.pop('username', None)
    if next:
        return redirect(next)
    return redirect(url_for('index'))

# Login-POST
# Query database for username:password combo
    # Query username, md5(password)
# If exist + correct redirect to logged in user's (own) feed (i.e. new render template)
# Query db again for user feed tweets
    # tweets gets formated through jinja2 in html

# Abstracted hash function
def hash_function(text):
    return md5(text).hexdigest()

# Basic query that gets back column from a table, if column is not specified, then * will be used
def basic_query(table, columns = '*'):
    if isinstance(columns, list):
        columns_string = ",".join(columns)
    elif isinstance(columns, str):
        columns_string = columns
    else:
        raise AttributeError
    # c.execute("SELECT * FROM {tn} WHERE {idf}=?".format(tn=table_name, cn=column_2, idf=id_column), (123456,))
    # subs = {'columns': columns_string, 'table': table}
    # query = 'SELECT columns=:columns FROM table=:table;'
    cursor = g.db.execute('SELECT {cn} FROM {tb};'.format(tb=table, cn=columns_string))
    query_result = cursor.fetchall()
    return query_result

# Basic insert, columns can be strings, but content has to be tuple matching string or tuple passed
def basic_insert(table, columns, content):
    if isinstance(columns, tuple):
        columns_tuple = columns
    elif isinstance(columns, str):
        columns_tuple = columns.split(',')
    else:
        raise AttributeError
        
    if len(content) != len(columns_tuple):
        raise ValueError
    else:
        # INSERT INTO "tweet" ("user_id", "content") VALUES (10, "Hello World!");
        cursor = g.db.execute('INSERT INTO \"{tb}\" {cn} VALUES \"{ct}\"'.format(tb=table, cn=columns_tuple, ct=content))
    return

# kwargs is the contents being updated, parameter is what we're trying to update (i.e. WHERE 'parameter') which should be a string of 'column = value'
def basic_update(table, parameter, **kwargs):
    # UPDATE Customers SET ContactName='Alfred Schmidt', City='Hamburg' WHERE CustomerName='Alfreds Futterkiste';
    
    # Check parameter format
    single_quote = "\'" #SQL requires single quotes
    if isinstance(parameter, str):
        equals_index = parameter.find('=')
        after_equals = parameter[equals_index+1]
        
        # If parameter value is not in quotes, put quotes around that value
        if after_equals != single_quote:
            first_quote_index = parameter.find(single_quote, after_equals)
            
            # Best case scenario: no quotes at all
            if first_quote_index == -1:
                # This gets the index right before an alphanumeric after the equals sign
                to_quote_index = equals_index + re.search('\w',parameter[equals_index:]).start()
                
                #Strings are immutable in py so using a list instead
                parameter_list = list(parameter) 
                parameter_list[to_quote_index] = single_quote
                parameter_list.append(single_quote)
                
                # Put list back into string
                parameter = "".join(parameter_list)
            else:
                # Too lazy to code edge cases atm
                raise ValueError
                
    else:
        raise AttributeError
    
    # Create a string from **kwargs of things to update
    content_list = ["{}='{}'".format(key,value) for key,value in kwargs.items()]
    content_string = ','.join(content_list)

    cursor = g.db.execute('UPDATE {tb} SET {ct} WHERE {param};'.format(tb=table, ct=content_string, param=parameter))

    return