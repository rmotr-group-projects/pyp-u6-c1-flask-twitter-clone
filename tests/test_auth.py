from hashlib import md5
from flask import session

from . import BaseTwitterCloneTestCase


class AuthenticationTestCase(BaseTwitterCloneTestCase):

    def test_login_get(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn('<form', response.data.decode('utf-8'))

    def test_not_authenticated_index_redirects_login(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('http://localhost/login', response.location)

        response = self.client.get('/', follow_redirects=True)
        self.assertIn('<form', response.data.decode('utf-8'))
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
                  'password': md5(u'donotexist'.encode('utf-8')).hexdigest()})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Invalid username or password',
                      response.data.decode('utf-8'))

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
