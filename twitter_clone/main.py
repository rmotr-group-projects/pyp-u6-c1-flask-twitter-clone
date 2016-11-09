import sqlite3
from hashlib import md5
from functools import wraps
from flask import Flask
from flask import (g, request, session, redirect, render_template,
                   flash, url_for, abort)

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
@app.route('/login', methods=['POST', 'GET'])
def login():
	if request.method == 'GET':
		if session.get('username', None) is not None:
			return redirect('/')
		else:
			return render_template('login.html')
	elif request.method == 'POST':
		username = request.form['username']
		password_hash = md5(request.form['password'].encode('utf-8')).hexdigest()
		cursor = g.db.execute("SELECT id, username FROM user WHERE username='{}' AND password='{}'".format(username, password_hash))
		record = cursor.fetchone()
		if record is not None:
			session['user_id'] = record[0]
			session['username'] = record[1]
			return redirect('/')
		else:
			flash('Invalid username or password.')
			return render_template('login.html')

@app.route('/<username>', methods=['POST', 'GET'])
def feed(username):
	if session.get('username', None) == username:
		#logged in as this user
		if request.method == 'POST':
			g.db.execute("""
				INSERT INTO "tweet" ("user_id", "content") 
				VALUES ({}, "{}");
			""".format(session['user_id'], request.form['tweet']))
			g.db.commit()

		cursor = g.db.execute("""
			SELECT t.id, u.username, t.created, t.content
			FROM tweet t INNER JOIN user u ON t.user_id = u.id
			WHERE u.username='{}'
		""".format(username))
		tweets = [dict(id=row[0], username=row[1], created=row[2], content=row[3])
				  for row in cursor.fetchall()]
		return render_template('own_feed.html', tweets=tweets)
	else:
		#read only feed
		if request.method == 'POST':
			abort(403)
		cursor = g.db.execute("""
			SELECT u.username, t.created, t.content
			FROM tweet t INNER JOIN user u ON t.user_id = u.id
			WHERE u.username='{}'
		""".format(username))
		tweets = [dict(username=row[0], created=row[1], content=row[2])
				  for row in cursor.fetchall()]
		return render_template('other_feed.html', tweets=tweets)


@app.route('/logout')
def logout():
	session.pop('user_id')
	session.pop('username')
	flash('You have been successfully logged out.')
	return redirect('/')


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
	if request.method == 'POST':
		g.db.execute("""
			UPDATE user
			SET first_name="{}", last_name="{}", birth_date="{}"
			WHERE id={}
		""".format(request.form['first_name'], request.form['last_name'], request.form['birth_date'], session['user_id']))
		g.db.commit()
		flash("Your profile has been updated.")
	cursor = g.db.execute("""
		SELECT username, first_name, last_name, birth_date
		FROM user
		""")
	row = cursor.fetchone()
	user_profile = dict(username=row[0], firt_name=row[1], last_name=row[2], birth_date=row[3])
	return render_template('profile.html', profile=user_profile)

@app.route('/tweets/<int:tweet_id>/delete', methods=['POST'])
@login_required
def delete_tweet(tweet_id):
	# check if tweet exists
	cursor = g.db.execute("SELECT id, user_id FROM tweet WHERE id={}".format(tweet_id))
	record = cursor.fetchone()
	if record is not None and record[1] == session['user_id']:
		g.db.execute("""
			DELETE FROM tweet
			WHERE id={};
		""".format(tweet_id))
		g.db.commit()
		flash("Tweet deleted.")
		return redirect('/')
	elif record[1] != session['user_id']:
		abort(403)
	else:
		abort(404)

@app.route('/')
@login_required
def site_root():
	return redirect('/{}'.format(session['username']))