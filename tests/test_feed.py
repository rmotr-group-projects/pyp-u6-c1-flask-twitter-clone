from twitter_clone.main import app
from . import BaseTwitterCloneTestCase


class FeedTestCase(BaseTwitterCloneTestCase):

    def test_feed_not_authenticated_readonly(self):
        response = self.client.get('/testuser1')
        self.assertEqual(response.status_code, 200)
        data = response.data.decode('utf-8')
        self.assertFalse('<form' in data)
        self.assertTrue('Tweet 1 testuser1' in data)
        self.assertTrue('Tweet 2 testuser1' in data)
        self.assertFalse('Tweet 1 testuser2' in data)

    def test_feed_authenticated_get(self):
        with app.test_client() as client:
            client.post(
                '/login',
                data={'username': 'testuser1', 'password': '1234'},
                follow_redirects=True)
            response = client.get('/testuser1')
            self.assertEqual(response.status_code, 200)
            data = response.data.decode('utf-8')
            self.assertTrue('<form' in data)
            self.assertEqual(data.count('<form'), 3)  # textarea and 2 tweet delete buttons
            self.assertTrue('Tweet 1 testuser1' in data)
            self.assertTrue('Tweet 2 testuser1' in data)
            self.assertFalse('Tweet 1 testuser2' in data)

    def test_feed_authenticated_get_other_users_feed(self):
        with app.test_client() as client:
            client.post(
                '/login',
                data={'username': 'testuser1', 'password': '1234'},
                follow_redirects=True)
            response = client.get('/testuser2')  # different as logged in
            self.assertEqual(response.status_code, 200)
            data = response.data.decode('utf-8')
            self.assertFalse('<form' in data)
            self.assertTrue('Tweet 1 testuser2' in data)
            self.assertFalse('Tweet 1 testuser1' in data)
            self.assertFalse('Tweet 2 testuser1' in data)

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
            data = response.data.decode('utf-8')
            self.assertEqual(data.count('<form'), 4)  # textarea and 3 tweet delete buttons
            self.assertTrue('<form' in data)
            self.assertTrue('Tweet 1 testuser1' in data)
            self.assertTrue('Tweet 2 testuser1' in data)
            self.assertTrue('This tweet is new' in data)
            self.assertFalse('Tweet 1 testuser2' in data)

    def test_feed_not_authenticated_post(self):
        response = self.client.post('/testuser1', data={'tweet': 'This tweet is new'})
        self.assertEqual(response.status_code, 403)
