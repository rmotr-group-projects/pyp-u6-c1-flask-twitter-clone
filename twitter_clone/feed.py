import sqlite3
from hashlib import md5
from modules import *
from functools import wraps
from flask import (g, request, session, redirect, render_template,
                   flash, url_for, abort)


@app.route('/<username>', methods=['GET'])
def feed(username):
    if 'username' not in session or session['username'] != username:
        return other_feed(username)
    else:
        return own_feed(username)


def own_feed(username):
    user_id = session['user_id']
    cur = g.db.cursor()
    cur.execute('SELECT id, content, created from tweet WHERE user_id = ? \
                ORDER BY id DESC',(user_id,))
    my_tweets = cur.fetchall()
    return render_template('static_templates/layout_own_feed.html',
                            username=username,tweets=my_tweets)


def other_feed(username):
    me = ''
    if 'username' in session:
        me = session['username']
    cur = g.db.cursor()
    cur.execute('SELECT id, username from user WHERE username = ?',
    (username,))
    fetched = cur.fetchone()
    user_id = fetched[0]
    user = fetched[1]

    cur.execute('SELECT id,content,created from tweet WHERE user_id = ? \
    ORDER BY id DESC',(user_id,))

    tweets = cur.fetchall()
    return render_template('static_templates/layout_other_feed.html',
                            me=me,username=user,tweets=tweets), 200