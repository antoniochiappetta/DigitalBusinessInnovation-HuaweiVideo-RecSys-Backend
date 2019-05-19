import unittest

from flask import jsonify
from base64 import b64encode
from app import create_app, db
from app.models import User
from tests.test_config import TestConfig


class ApiCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    ############
    # User API
    ############

    def testCreateUser(self):
        u = User(id=1, username='u', firstName='f', lastName='l', email='e')
        u.set_password('p')
        rv = self.client.post('/api/user', json={
            'username': u.username,
            'firstName': u.firstName,
            'lastName': u.lastName,
            'email': u.email,
            'password': 'p',
        })

        self.assertEqual(201, rv.status_code)
        self.assertDictEqual(jsonify(u.to_dict()).get_json(), rv.get_json())

    def testFailedCreateUser(self):
        rv = self.client.post('/api/user', json={
            'username': 'u',
            'firstName': 'f',
            'lastName': 'l'
        })

        self.assertEqual(405, rv.status_code)
        self.assertEqual('Invalid input', rv.get_json()['type'])

    def testDuplicatedUser(self):
        u = User(id=1, username='u', firstName='f', lastName='l', email='e')
        db.session.add(u)
        db.session.commit()

        u.set_password('p')
        rv = self.client.post('/api/user', json={
            'username': u.username,
            'firstName': u.firstName,
            'lastName': u.lastName,
            'email': u.email,
            'password': 'p',
        })

        self.assertEqual(405, rv.status_code)
        self.assertEqual('Invalid input', rv.get_json()['type'])

    ############
    # Token API
    ############
    def _fixture_get_token(self):
        u = User(id=1, username='u', firstName='f', lastName='l', email='e')
        u.set_password('p')
        db.session.add(u)
        db.session.commit()

        user_pass = b64encode(b"u:p").decode("ascii")
        headers = {'Authorization': 'Basic %s' % user_pass}

        rv = self.client.post('/api/token', headers=headers)
        return rv, u

    def testCreateToken(self):
        rv, _ = self._fixture_get_token()
        self.assertEqual(200, rv.status_code)
        self.assertEqual(1, rv.get_json()['sub'])

    def testGetUser(self):
        rv, u = self._fixture_get_token()
        rv1 = self.client.get('/api/user/' + str(rv.get_json()['sub']),
                              headers={'Authorization': 'Bearer %s' % rv.get_json()['token']})
        self.assertEqual(200, rv1.status_code)
        self.assertEqual(u.to_dict(), rv1.get_json())

    def testFailedGetUserMissingToken(self):
        rv, u = self._fixture_get_token()
        rv1 = self.client.get('/api/user/' + str(rv.get_json()['sub']))
        self.assertEqual(401, rv1.status_code)

    def testFailedGetUserWrongToken(self):
        rv, u = self._fixture_get_token()
        rv1 = self.client.get('/api/user/' + str(rv.get_json()['sub']),
                              headers={'Authorization': 'Bearer %s' % 'wrong_token'})
        self.assertEqual(401, rv1.status_code)

    def testDeleteToken(self):
        rv, u = self._fixture_get_token()
        rv_delete = self.client.delete('/api/token',
                                       headers={'Authorization': 'Bearer %s' % rv.get_json()['token']})
        self.assertEqual(204, rv_delete.status_code)

        # Try to get user with same token now
        rv_get = self.client.get('/api/user/' + str(rv.get_json()['sub']),
                                 headers={'Authorization': 'Bearer %s' % rv.get_json()['token']})
        self.assertEqual(401, rv_get.status_code)
