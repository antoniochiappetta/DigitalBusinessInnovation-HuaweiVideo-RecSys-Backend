import unittest

from flask import jsonify
from base64 import b64encode
from app import create_app, db
from app.models import User, Movie
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

    ############
    # Movie API
    ############

    def testGetTopPop(self):
        rv, u = self._fixture_get_token()

        movies = []
        for i in range(3):
            movies.append(Movie(title='t%d' % i, description='d%d' % i))
            db.session.add(movies[i])

        users = []
        for i in range(3):
            users.append(User())
            users[i].watch(movies[i % 2])
            db.session.add(users[i])

        db.session.commit()

        expected = {
            '_links': {'next': None, 'prev': None, 'self': '/api/movie/toppop?page=1&per_page=10'},
            '_meta': {'page': 1, 'per_page': 10, 'total_items': 2, 'total_pages': 1},
            'items': [
                {'_links': {'self': 'http://localhost:5000/api/movie/1', 'video': None},
                 'description': 'd0', 'id': 1, 'rating': {'score': 0.0, 'support': 0}, 'title': 't0'},
                {'_links': {'self': 'http://localhost:5000/api/movie/2', 'video': None},
                 'description': 'd1', 'id': 2, 'rating': {'score': 0.0, 'support': 0}, 'title': 't1'},
            ]
        }

        rv_toppop = self.client.get('/api/movie/toppop',
                                    headers={'Authorization': 'Bearer %s' % rv.get_json()['token']})

        self.assertEqual(200, rv_toppop.status_code)
        self.assertEqual(expected, rv_toppop.get_json())

    def testEmptyGetWatchedMovie(self):
        rv, u = self._fixture_get_token()
        rv_watched = self.client.get('/api/movie/watched/%d' % u.id,
                                     headers={'Authorization': 'Bearer %s' % rv.get_json()['token']})

        expected = {
            '_links': {'next': None, 'prev': None, 'self': '/api/movie/watched/1?page=1&per_page=10'},
            '_meta': {'page': 1, 'per_page': 10, 'total_items': 0, 'total_pages': 0},
            'items': []
        }

        self.assertEqual(200, rv_watched.status_code)
        self.assertEqual(expected, rv_watched.get_json())

    def testGetWatchedMovie(self):
        rv, u = self._fixture_get_token()
        m1 = Movie(id=1, title='t1', description='d1')
        m2 = Movie(id=2, title='t2', description='d2')
        u.watch(m2)
        db.session.add(m1)
        db.session.add(m2)
        db.session.commit()
        rv_watched = self.client.get('/api/movie/watched/%d' % u.id,
                                     headers={'Authorization': 'Bearer %s' % rv.get_json()['token']})

        expected = {
            '_links': {'next': None, 'prev': None, 'self': '/api/movie/watched/1?page=1&per_page=10'},
            '_meta': {'page': 1, 'per_page': 10, 'total_items': 1, 'total_pages': 1},
            'items': [
                {'_links': {'self': 'http://localhost:5000/api/movie/2', 'video': None},
                 'description': 'd2', 'id': 2, 'rating': {'score': 0.0, 'support': 0}, 'title': 't2'},
            ]
        }

        self.assertEqual(200, rv_watched.status_code)
        self.assertEqual(expected, rv_watched.get_json())

    def testGetMovie(self):
        rv, u = self._fixture_get_token()

        m = Movie(title='t', description='d')
        db.session.add(m)
        db.session.commit()

        rv_watched = self.client.get('/api/movie/%d' % m.id,
                                     headers={'Authorization': 'Bearer %s' % rv.get_json()['token']})

        expected = {
            '_links': {'self': 'http://localhost:5000/api/movie/1', 'video': None},
            'description': 'd',
            'id': 1,
            'rating': {'score': 0.0, 'support': 0},
            'title': 't'
        }

        self.assertEqual(200, rv_watched.status_code)
        self.assertEqual(expected, rv_watched.get_json())