try:
    from .login import login, login_required
except ValueError:
    from twitter_clone.login import login, login_required

try:
    from .feed import other_feed, own_feed, feed
except ValueError:
    from twitter_clone.feed import other_feed, own_feed, feed

try:
    from .modules import app
except ValueError:
    from twitter_clone.modules import app

import sqlite3
from hashlib import md5
from functools import wraps
from flask import (g, request, session, redirect, render_template,
                   flash, url_for, abort)

def connect_db(db_name):
    return sqlite3.connect(db_name)

@app.before_request
def before_request():
    g.db = connect_db(app.config['DATABASE'][1])

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('feed',username=session['username']))
    else:
        return redirect(url_for('login'))

@app.route('/<username>', methods=['POST'])
def post_tweet(username):
    if 'username' not in session or username != session['username']:
        abort(403)
    cur = g.db.cursor()
    tweet = request.form['tweet']
    user_id = session['user_id']
    cur.execute('INSERT INTO tweet ("user_id","content") VALUES (?, ?)',
                (user_id, tweet))
    g.db.commit()
    cur.execute('SELECT id, content, created FROM tweet WHERE user_id = ? \
                ORDER BY id DESC',(user_id,))
    my_tweets = cur.fetchall()
    flash('You have successfully posted a new Tweet.')
    return render_template('static_templates/layout_own_feed.html',username=username,
                            tweets=my_tweets)

@app.route('/tweets/<int:tweet_id>/delete', methods=['POST'])
@login_required
def delete_tweet(tweet_id):
    if 'username' not in session:
        abort(403)
    cur = g.db.cursor()
    user_id = session['user_id']
    cur.execute('DELETE from tweet WHERE id = ? AND user_id = ?',
                (tweet_id,user_id))
    g.db.commit()
    flash('Tweet deleted.')
    return redirect(url_for('home'))


@app.route('/logout')
@login_required
def logout():
    session['logged_in'] = False
    session.pop('username', None)
    session.pop('user_id', None)
    flash('You have successfully logged out.')
    return redirect(url_for('home'))


@app.route('/profile', methods = ['GET'])
@login_required
def profile():
    return render_template('static_templates/layout_profile.html',
                            username = session['username'],
                            birth_date = session['bdate'],
                            first_name = session['fname'],
                            last_name = session['lname'])


@app.route('/profile', methods=['POST'])
@login_required
def edit_profile():
    cur = g.db.cursor()

    session['fname'] = request.form['first_name']
    session['lname'] = request.form['last_name']
    session['bdate'] = request.form['birth_date']

    cur.execute('''UPDATE user SET "first_name" = ?, "last_name" = ?,
                                   "birth_date" = ? WHERE "username" = ?'''
    ,(session['fname'],session['lname'],session['bdate'],session['username']))
    g.db.commit()
    return render_template('static_templates/layout_profile.html',
                            username = session['username'],
                            birth_date = session['bdate'],
                            first_name =session['fname'],
                            last_name = session['lname'])