import unittest

from flask import jsonify
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
