import os
import unittest
import tempfile
from hashlib import md5

from twitter_clone.main import app, connect_db
from twitter_clone import settings


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
        self.db.execute('INSERT INTO "user" ("id", "username", "password") VALUES (1, "testuser1", "{}");'.format(md5(u'1234'.encode('utf-8')).hexdigest()))
        self.db.execute('INSERT INTO "user" ("id", "username", "password") VALUES (2, "testuser2", "{}");'.format(md5(u'1234'.encode('utf-8')).hexdigest()))
        self.db.execute('INSERT INTO "user" ("id", "username", "password") VALUES (3, "testuser3", "{}");'.format(md5(u'1234'.encode('utf-8')).hexdigest()))
        self.db.execute('INSERT INTO "tweet" ("id", "user_id", "content") VALUES (1, 1, "Tweet 1 testuser1");')
        self.db.execute('INSERT INTO "tweet" ("id", "user_id", "content") VALUES (2, 1, "Tweet 2 testuser1");')
        self.db.execute('INSERT INTO "tweet" ("id", "user_id", "content") VALUES (3, 2, "Tweet 1 testuser2");')
        self.db.commit()
