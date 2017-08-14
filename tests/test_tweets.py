# -*- coding: utf-8 -*-
from twitter_clone.main import app
from . import BaseTwitterCloneTestCase


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
