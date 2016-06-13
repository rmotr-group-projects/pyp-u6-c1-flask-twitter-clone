# -*- coding: utf-8 -*-
import os
import unittest
import tempfile
from hashlib import md5

from flask import session

from twitter_clone import settings
from twitter_clone.main import app, connect_db


class BaseTwitterCloneTestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'testing secret key'
        app.config['DATABASE'] = tempfile.mkstemp()

        # set up testing database
        db = connect_db(db_name=app.config['DATABASE'][1])
        self.db = db
        self.load_fixtures()

        self.client = app.test_client()

    def load_fixtures(self):
        with open(os.path.join(settings.BASE_DIR, 'twitter-schema.sql'), 'r') as f:
            sql_query = f.read()
        for statement in sql_query.split(';'):
            self.db.execute(statement)
        self.db.execute('INSERT INTO "user" ("id", "username", "password") VALUES (1, "testuser1", "{}");'.format(md5('1234'.encode('utf-8')).hexdigest()))
        self.db.execute('INSERT INTO "user" ("id", "username", "password") VALUES (2, "testuser2", "{}");'.format(md5('1234'.encode('utf-8')).hexdigest()))
        self.db.execute('INSERT INTO "user" ("id", "username", "password") VALUES (3, "testuser3", "{}");'.format(md5('1234'.encode('utf-8')).hexdigest()))
        self.db.execute('INSERT INTO "tweet" ("user_id", "content") VALUES (1, "Tweet 1 testuser1");')
        self.db.execute('INSERT INTO "tweet" ("user_id", "content") VALUES (1, "Tweet 2 testuser1");')
        self.db.execute('INSERT INTO "tweet" ("user_id", "content") VALUES (2, "Tweet 1 testuser2");')
        self.db.commit()


class AuthenticationTestCase(BaseTwitterCloneTestCase):

    def test_login_get(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn('<form'.encode('utf-8'), response.data)

    def test_not_authenticated_index_redirects_login(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('http://localhost/login', response.location)

        response = self.client.get('/', follow_redirects=True)
        self.assertIn('<form'.encode('utf-8'), response.data)
        self.assertEqual(response.status_code, 200)

    def test_authenticated_login_redirects_next(self):
        with app.test_client() as client:
            client.post('/login',
                        data={'username': 'testuser1',
                              'password': '1234'},
                        follow_redirects=True)
            response = client.get('/login')
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.location, 'http://localhost/')

    def test_login_user_does_not_exist(self):
        response = self.client.post(
            '/login',
            data={'username': 'donotexist',
                  'password': md5('donotexist'.encode('utf-8')).hexdigest()})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Invalid username or password'.encode('utf-8'), response.data)

    def test_login_correct(self):
        with app.test_client() as client:
            response = client.post(
                '/login',
                data={'username': 'testuser1', 'password': '1234'},
                follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(session['user_id'], 1)
            self.assertEqual(session['username'], 'testuser1')

    def test_logout(self):
        with app.test_client() as client:
            response = client.post(
                '/login',
                data={'username': 'testuser1', 'password': '1234'},
                follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(session['user_id'], 1)
            self.assertEqual(session['username'], 'testuser1')

            response = client.get('/logout')
            self.assertEqual(response.status_code, 302)
            self.assertEqual('http://localhost/', response.location)
            self.assertFalse('user_id' in session)
            self.assertFalse('username' in session)


class FeedTestCase(BaseTwitterCloneTestCase):

    def test_feed_not_authenticated_readonly(self):
        response = self.client.get('/testuser1')
        self.assertEqual(response.status_code, 200)
        self.assertFalse('<form'.encode('utf-8') in response.data)
        self.assertTrue('Tweet 1 testuser1'.encode('utf-8') in response.data)
        self.assertTrue('Tweet 2 testuser1'.encode('utf-8') in response.data)
        self.assertFalse('Tweet 1 testuser2'.encode('utf-8') in response.data)

    def test_feed_authenticated_get(self):
        with app.test_client() as client:
            client.post(
                '/login',
                data={'username': 'testuser1', 'password': '1234'},
                follow_redirects=True)
            response = client.get('/testuser1')
            self.assertEqual(response.status_code, 200)
            self.assertTrue('<form'.encode('utf-8') in response.data)
            self.assertEqual(response.data.count('<form'.encode('utf-8')), 3)  # textarea and 2 tweet delete buttons
            self.assertTrue('Tweet 1 testuser1'.encode('utf-8') in response.data)
            self.assertTrue('Tweet 2 testuser1'.encode('utf-8') in response.data)
            self.assertFalse('Tweet 1 testuser2'.encode('utf-8') in response.data)

    def test_feed_authenticated_get_other_users_feed(self):
        with app.test_client() as client:
            client.post(
                '/login',
                data={'username': 'testuser1', 'password': '1234'},
                follow_redirects=True)
            response = client.get('/testuser2')  # different as logged in
            self.assertEqual(response.status_code, 200)
            self.assertFalse('<form'.encode('utf-8') in response.data)
            self.assertTrue('Tweet 1 testuser2'.encode('utf-8') in response.data)
            self.assertFalse('Tweet 1 testuser1'.encode('utf-8') in response.data)
            self.assertFalse('Tweet 2 testuser1'.encode('utf-8') in response.data)

    def test_feed_authenticated_post(self):
        with app.test_client() as client:
            client.post(
                '/login',
                data={'username': 'testuser1', 'password': '1234'},
                follow_redirects=True)
            response = client.post('/testuser1', data={'tweet': 'This tweet is new'})
            self.assertEqual(response.status_code, 200)
            cursor = self.db.execute("select * from tweet where user_id = 1;")
            self.assertEqual(len(cursor.fetchall()), 3)
            self.assertTrue('<form'.encode('utf-8') in response.data)
            self.assertEqual(response.data.count('<form'.encode('utf-8')), 4)  # textarea and 3 tweet delete buttons
            self.assertTrue('Tweet 1 testuser1'.encode('utf-8') in response.data)
            self.assertTrue('Tweet 2 testuser1'.encode('utf-8') in response.data)
            self.assertTrue('This tweet is new'.encode('utf-8') in response.data)
            self.assertFalse('Tweet 1 testuser2'.encode('utf-8') in response.data)

    def test_feed_not_authenticated_post(self):
        response = self.client.post('/testuser1', data={'tweet': 'This tweet is new'})
        self.assertEqual(response.status_code, 403)


class ProfileTestCase(BaseTwitterCloneTestCase):

    def test_profile_not_authenticated_redirects_login(self):
        response = self.client.get('/profile')
        self.assertEqual(response.status_code, 302)
        self.assertTrue('http://localhost/login' in response.location)

    def test_profile_authenticated_get(self):
        with app.test_client() as client:
            client.post(
                '/login',
                data={'username': 'testuser1', 'password': '1234'},
                follow_redirects=True)
            response = client.get('/profile')
            self.assertEqual(response.status_code, 200)
            self.assertIn('<form'.encode('utf-8'), response.data)
            self.assertIn('testuser1'.encode('utf-8'), response.data)

    def test_profile_authenticated_post(self):
        with app.test_client() as client:
            client.post(
                '/login',
                data={'username': 'testuser1', 'password': '1234'},
                follow_redirects=True)
            response = client.post(
                '/profile',
                data={'username': 'testuser1',
                      'first_name': 'Test',
                      'last_name': 'User',
                      'birth_date': '2016-01-30'})
            self.assertEqual(response.status_code, 200)
            profile = self.db.execute("select * from user where id = 1;").fetchone()
            expected = (1, u'testuser1', u'81dc9bdb52d04dc20036dbd8313ed055',
                        u'Test', u'User', '2016-01-30')
            self.assertEqual(profile, expected)


class TweetsTestCase(BaseTwitterCloneTestCase):

    def test_delete_tweet_authenticated(self):
        with app.test_client() as client:
            client.post(
                '/login',
                data={'username': 'testuser1', 'password': '1234'},
                follow_redirects=True)

            # pre condition, must be 2 tweets
            cursor = self.db.execute("select * from tweet where user_id = 1;")
            self.assertEqual(len(cursor.fetchall()), 2)

            # delete tweet with id=1
            response = client.post('/tweets/1/delete')
            self.assertEqual(response.status_code, 302)
            self.assertEqual('http://localhost/', response.location)

            cursor = self.db.execute("select * from tweet where user_id = 1;")
            self.assertEqual(len(cursor.fetchall()), 1)

    def test_delete_tweet_not_authenticated_redirects_login(self):
        response = self.client.post('/tweets/1/delete')
        self.assertEqual(response.status_code, 302)
        self.assertIn('http://localhost/login', response.location)

    def test_delete_tweet_invalid_id(self):
        response = self.client.post('/tweets/invalid/delete')
        self.assertEqual(response.status_code, 404)
