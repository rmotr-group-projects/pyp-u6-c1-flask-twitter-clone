import sqlite3
from .modules import app
from hashlib import md5
from functools import wraps
from flask import (g, request, session, redirect, render_template,
                   flash, url_for, abort)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('home'))
    cur = g.db.cursor()
    if request.method == 'POST':
        user = request.form['username']
        pw = md5(request.form['password'].encode('utf-8')).hexdigest()
        cur.execute('SELECT * from user WHERE username = ? AND password = ?',
                    (user, pw))

        fetched = cur.fetchone()
        if fetched is None:
            return "Invalid username or password"
        fetched = list(fetched)
        fetched.pop(2)

        session['logged_in'] = True
        check_for = ['user_id','username','fname','lname','bdate']
        for idx, check in enumerate(check_for):
            session[check] = fetched[idx]
        flash('You have successfully logged in.')
        return redirect(url_for('feed',username=session['username']))
    return render_template('static_templates/layout_login.html')


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function