import unittest

from app import create_app, db
from app.models import User, Movie, Interaction
from tests.test_config import TestConfig


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
        m = Movie(title='Pulp Fiction', description='John Travolta\'s movie')

        db.session.add(u)
        db.session.add(m)
        db.session.commit()

        self.assertEqual(u.watched_movies, [])
        self.assertEqual(m.spectators, [])

        u.watch(m)
        db.session.commit()
        self.assertTrue(u.has_watched(m))
        self.assertEqual(len(u.watched_movies), 1)
        self.assertEqual(u.watched_movies[0].movie.title, 'Pulp Fiction')
        self.assertEqual(len(m.spectators), 1)
        self.assertEqual(m.spectators[0].user.username, 'john')

    def test_update_rate(self):
        u = User()
        m = Movie()
        u.watch(m)

        db.session.add(u)
        db.session.add(m)
        db.session.commit()
        self.assertEqual((0.0, 0), Interaction.compute_explicit_rate(m.id))

        u.watch_rate(m, 2.0)
        db.session.commit()
        self.assertEqual((2.0, 1), Interaction.compute_explicit_rate(m.id))

        u.watch_rate(m, Interaction.IMPLICIT_RATE)
        db.session.commit()
        self.assertEqual((2.0, 1), Interaction.compute_explicit_rate(m.id))

    def test_compute_score(self):
        u1 = User()
        u2 = User()
        u3 = User()
        m = Movie(title='Pulp Fiction', description='John Travolta\'s movie')
        u1.watch_rate(m, 1.0)
        u2.watch(m)
        u3.watch_rate(m, 5.0)

        db.session.add(u1)
        db.session.add(u2)
        db.session.add(m)
        db.session.commit()

        score, support = Interaction.compute_explicit_rate(m.id)
        self.assertEqual(2, support)
        self.assertEqual(3.0, score)

    def test_user_to_dict(self):
        u = User(username='T', firstName='F', lastName='L', email='e')
        db.session.add(u)
        db.session.commit()

        json = {'id': 1, 'username': 'T', 'firstName': 'F', 'lastName': 'L', 'email': 'e',
                '_links': {
                    'self': 'http://localhost:5000/api/user/1',
                    'recommended_movies': 'http://localhost:5000/api/movie/recommended/1',
                    'watched_movies': 'http://localhost:5000/api/movie/watched/1'}}

        self.assertEqual(json, u.to_dict(include_email=True))

    def test_movie_to_dict(self):
        m = Movie(title='T', description='D', imdb_id='2', tmdb_id='4', ytbe_id='v')
        db.session.add(m)
        db.session.commit()

        json = {'id': 1, 'imdbId': 2, 'tmdbId': 4, 'ytbeId': 'v', 'title': 'T', 'description': 'D',
            'rating': {
                'score': 0.0,
                'support': 0
            },
            '_links': {
                'self': 'http://localhost:5000/api/movie/1'
            }
        }

        self.assertEqual(json, m.to_dict())

    def test_token(self):
        u = User(username='utoken')
        t = u.get_token()
        db.session.add(u)
        db.session.commit()
        self.assertEqual(u, User.check_token(t))

        u.revoke_token()
        db.session.commit()
        self.assertIsNone(User.check_token(t))


if __name__ == '__main__':
    unittest.main(verbosity=1)
