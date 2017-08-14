# -*- coding: utf-8 -*-
from twitter_clone.main import app
from . import BaseTwitterCloneTestCase


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
            data = response.data.decode('utf-8')
            self.assertIn('<form', data)
            self.assertIn('testuser1', data)

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
