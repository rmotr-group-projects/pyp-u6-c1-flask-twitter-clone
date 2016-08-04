import sqlite3
from hashlib import md5
from functools import wraps
from flask import Flask
from flask import (g, request, session, redirect, render_template,
                   flash, url_for, abort)
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



# Index view ###################################################################
@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('feed', username=session['username']))
    return redirect(url_for('login'))


# Login view ###################################################################
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    users = basic_query('user', 'username, password, id')
    
    if request.method == 'POST':
        username = request.form['username']
        password = hash_function(request.form['password'])

        '''Hard coded user query'''
        # query = 'SELECT username, password FROM user '#WHERE username=:username;'
        # subs = {'username': username}
        # cursor = g.db.execute(query)
        # users = cursor.fetchall()
        
        for user in users:
            if user[0] == username and user[1] == password:
                session['username'] = username
                session['user_id'] = user[2]
                flash('You were logged in')
                return redirect(url_for('index'))
        error = 'Invalid username or password'
    if request.method == "GET":
        # Might need extra checks to be extra prudent with logging in/sessions
        if 'username' in session:
            return redirect(url_for('index'))
    return render_template('login.html', error=error)
    
    
    
# Profile view #################################################################
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    succesful_profile_update = None
    if request.method == 'POST':
        form = request.form
        
        '''Hard coded update'''
        query = 'UPDATE user SET first_name = "{}", last_name = "{}", birth_date = \
        "{}" WHERE username = "{}"'.format(form['first_name'], form['last_name'], \
        form['birth_date'], session['username'])
        
        g.db.execute(query)
        g.db.commit()
        
        succesful_profile_update = "Your profile was correctly updated"
        
    
    user_data = {}
    users = basic_query('user', 'username, first_name, last_name, birth_date')
    #print(users)
    for user in users:
        if session['username'] == user[0]:
            user_data = {'username':user[0], 'first_name':user[1], 'last_name':user[2], 'birth_date':user[3]}
             
    return render_template('profile.html', user=user_data, success = succesful_profile_update)


# Tweets view ##################################################################
# I don't think POST actually happens here, does it?  C: I think it gave me an error if I didnt include it
@app.route('/tweets/<int:tweet_id>/delete', methods=['GET', 'POST'])
@login_required
def tweets(tweet_id):
    # try:
    #     tweet_id = int(tweet_i)d
    # except:
    #     pass 
    # print("404 error check:" + str(type(tweet_id)))
    # if not isinstance(tweet_id,int):
    #     abort(404)
    print basic_query('tweet')
    # ('tweet', 'user_id, created, content, id')
    user_tweets = get_user_tweets(session['user_id'])
    deletion_query = 'DELETE FROM tweet WHERE id = ?;'
    for tweet in user_tweets:
        print(tweet, tweet_id)
        if tweet['tweet_id'] == tweet_id:
            print(tweet, tweet_id)
            g.db.execute(deletion_query, [tweet_id])
            g.db.commit()
    return redirect(url_for('index'))
            
    
    
'''      
    tweet_id = (tweet_id,)
    
    #test = g.db.execute("select * from tweet where user_id = {};".format(session['user_id']))
    #print(len(test.fetchall()))
    
    #query = 'SELECT id, user_id FROM tweet WHERE user_id ='+ str(session['user_id']) +';'

 
    query = 'SELECT id, user_id FROM tweet WHERE user_id = ?;'
    list_tweet_user_ids = g.db.execute(query,(str(session['user_id']),)).fetchall()
    for tweet_user_ids in list_tweet_user_ids:
        if tweet_user_ids[0] == int(tweet_id[0]):
            query = 'DELETE FROM tweet WHERE id = ?;'
            g.db.execute(query, tweet_id)
            g.db.commit()
            
    #test1 = g.db.execute("select * from tweet where user_id = {};".format(session['user_id']))
    #print("Number1:", len(test1.fetchall()))
    
    return redirect(url_for('index')) #redirect(url_for('feed',username=session['username']))
'''

# Feed view ####################################################################
@app.route('/<username>', methods=['GET', 'POST'])
def feed(username):
    
    ### Gets user Tweets ###
    user_id = None
    # Returns a list of tuples with (unicode) username and user_id
    users = basic_query('user', 'username, id')
    # Loop through the list of tuples and check to see if the <username> is in it
    for user in users:
        if username == user[0]:
            # if username is in it, let's assign that usernames id to the local user_id variable
            user_id = user[1]
    
    user_tweets = get_user_tweets(user_id)

    ### User Tweeting ###
    #print("This is the form:" + request.form)
    # i think the error can be fixed for the test case of 302 != 403 if we put a condition to check to see
    # if request.form['username'] == session['username']
    # We need to set up error handling using abort(), I pasted the link that way ---->
    if request.method == 'POST':
        
        # There's probably a more elegant way of doing this..
        try:
            if username != session['username']:
                abort(403)
        except:
            abort(403)
            
        tweet_text = str(request.form['tweet'])

        '''Hard coded version'''
        # print('INSERT INTO tweet (user_id, content) VALUES ' + str((user_id,tweet_text)) + ';')
        # g.db.execute('INSERT INTO tweet (user_id, content) VALUES ' + str((user_id,tweet_text)) + ';')
        # g.db.commit()
        
        basic_insert('tweet', '(user_id, content)', (user_id,tweet_text))
        
        user_tweets = get_user_tweets(user_id)
        return render_template('own_feed.html', username=session['username'], tweets=user_tweets)
        
    
    # WHY DO WE NEED THE EXTRA CONDITION TO CHECK IF USERNAME IS IN SESSION? DOESNT THE OTHER ONE DO IT ALREADY?
    # Yeah, I think it's redundant
    if 'username' in session and session['username'] == username:
        return render_template('own_feed.html', username=session['username'], tweets=user_tweets)
    elif 'username' in session:
        return render_template('other_feed.html', username=session['username'], tweet_user=username, tweets=user_tweets)
    else:
        return render_template('other_feed.html', username=None, tweet_user=username, tweets=user_tweets)

        
# Logout view ##################################################################
@app.route('/logout')
def logout(next=None):
    print(session)
    session.pop('username', None)
    session.pop('user_id', None)
    if next:
        return redirect(next)
    return redirect(url_for('index'))


# Abstracted hash function #####################################################
def hash_function(text):
    return md5(text).hexdigest()


# Function to get a list of dict tweets for a specific user
def get_user_tweets(user_id):
    # Return all tweets (for all users! just because we love Python)
    all_tweets = basic_query('tweet', 'user_id, created, content, id')
    # We're gonna store some tweets for a specific user in this list
    user_tweets = []
    for tweet in all_tweets:
        # If the user_id that we defined earlier is in the row for an entry in
        # then add this tweet to the user_tweets
        if user_id == tweet[0]:
            user_tweets.append({'created':tweet[1], 'content':tweet[2], 'tweet_id':tweet[3]})
    return user_tweets[::-1]


# Determines whether a piece of data is string or some iterable type, returns string if iterable, raise error if not string or iterable type
def string_transform(data, iterable_type):
    if isinstance(data, iterable_type):
        return ",".join(data)
    elif isinstance(data, str):
        return data
    else:
        raise AttributeError


# Basic query that gets back column from a table, if column is not specified, then * will be used
def basic_query(table, columns = '*'):
    columns_string = string_transform(columns, list)
    # c.execute("SELECT * FROM {tn} WHERE {idf}=?".format(tn=table_name, cn=column_2, idf=id_column), (123456,))
    cursor = g.db.execute('SELECT {cn} FROM {tb};'.format(tb=table, cn=columns_string))
    query_result = cursor.fetchall()
    return query_result


# Basic insert, columns can be strings, but content has to be tuple matching string or tuple passed
def basic_insert(table, columns, content):
    '''Not working for tuples passed right now'''
    columns_string = string_transform(columns, tuple)
    columns_length = len(columns_string.split(','))

    if len(content) != columns_length:
        raise ValueError
    else:
        # INSERT INTO "tweet" ("user_id", "content") VALUES (10, "Hello World!");
        g.db.execute('INSERT INTO {tb} {cn} VALUES {ct};'.format(tb=table, cn=columns_string, ct=content))
        g.db.commit()
        #g.db.execute('INSERT INTO ? ? VALUES ?;' (table, columns_tuple, content))
    return


# Used by basic_update() to properly enclose strings in quotes
def transform_update_string(parameter):
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
                return parameter
            else:
                # Too lazy to code edge cases atm
                raise ValueError
                
    else:
        raise AttributeError
 
'''Doesn't work because birthday might be date time object? Might need extra logic to sanitize'''
# kwargs is the contents being updated, parameter is what we're trying to update 
# (i.e. WHERE 'parameter') which should be a string of 'column = value'
def basic_update(table, parameter, **kwargs):
    # UPDATE Customers SET ContactName='Alfred Schmidt', City='Hamburg' WHERE CustomerName='Alfreds Futterkiste';
    
    parameter_string = transform_update_string(parameter)
    
    # Create a string from **kwargs of things to update
    content_list = ["{}='{}'".format(key,value) for key,value in kwargs.items()]
    content_string = ','.join(content_list)

    g.db.execute('UPDATE {tb} SET {ct} WHERE {param};'.format(tb=table, ct=content_string, param=parameter_string))
    g.db.commit()
    return