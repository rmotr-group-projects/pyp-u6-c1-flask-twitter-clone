import sqlite3
from hashlib import md5
from flask import g
import re

# Abstracted hash function #####################################################
def hash_function(text):
    return md5(text.encode('utf-8')).hexdigest()

# Function to get a list of dict of tweets for a specific user #################
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