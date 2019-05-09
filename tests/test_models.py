import unittest

from app import create_app, db
from app.models import User, Movie
from tests import TestConfig


class UserModelCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        u = User(username='susan')
        u.set_password('cat')
        self.assertFalse(u.check_password('dog'))
        self.assertTrue(u.check_password('cat'))

    def test_watch(self):
        u = User(username='john')
        u.set_password('a')
        m = Movie(title='Pulp Fiction', description='John Travolta\'s movie')

        db.session.add(u)
        db.session.add(m)
        db.session.commit()

        self.assertEqual(u.watched_movies.all(), [])
        self.assertEqual(m.spectators.all(), [])

        u.watch(m)
        db.session.commit()
        self.assertTrue(u.has_watched(m))
        self.assertEqual(u.watched_movies.count(), 1)
        self.assertEqual(u.watched_movies.first().title, 'Pulp Fiction')
        self.assertEqual(m.spectators.count(), 1)
        self.assertEqual(m.spectators.first().username, 'john')

        u.un_watch(m)
        db.session.commit()
        self.assertFalse(u.has_watched(m))
        self.assertEqual(u.watched_movies.count(), 0)
        self.assertEqual(m.spectators.count(), 0)


if __name__ == '__main__':
    unittest.main(verbosity=1)
