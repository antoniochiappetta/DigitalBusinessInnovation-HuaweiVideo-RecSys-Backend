from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import url_for
from sqlalchemy import func
from app import db, login


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    firstName = db.Column(db.String(64), index=True, unique=True)
    lastName = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    watched_movies = db.relationship('Interaction', back_populates='user')
    
    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def watch(self, movie):
        self.watch_rate(movie, Interaction.IMPLICIT_RATE)

    def watch_rate(self, movie, score):
        if not self.has_watched(movie):
            i = Interaction()
            i.movie = movie
            i.score = score
            self.watched_movies.append(i)
        elif score != Interaction.IMPLICIT_RATE:
            i = Interaction.query.filter(
                Interaction.user_id == self.id,
                Interaction.movie_id == movie.id).first()
            i.score = score

    def has_watched(self, movie):
        return Interaction.query.filter(
            Interaction.user_id == self.id,
            Interaction.movie_id == movie.id).count() > 0

    def to_dict(self, include_email=False):
        data = {
            'id': self.id,
            'username': self.username,
            'firstName': self.firstName,
            'lastName': self.lastName,
            '_links': {
                'self': url_for('api.get_user', id=self.id),
                'watched_movies': url_for('api.get_watched_movies', id=self.id),
                'recommended_movies': url_for('api.get_recommended_movies', id=self.id)
            }
        }
        if include_email:
            data['email'] = self.email
        return data

    def from_dict(self, data, new_user=False):
        fields = ['username', 'email']
        if new_user:
            fields.append(['firstName', 'lastName'])
        for field in ['username', 'email']:
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])


# Helper for LoginManager to load users from model
@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), index=True, unique=True)
    description = db.Column(db.Text())
    video = db.Column(db.String(64))
    spectators = db.relationship('Interaction', back_populates='movie')

    def __repr__(self):
        return '<Movie {}>'.format(self.title)

    def to_dict(self):
        score, support = Interaction.compute_explicit_rate(self.id)
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'rating': {
                'score': score,
                'support': support
            },
            '_links': {
                'self': url_for('api.get_movie', id=self.id),
                'video': self.video
            }
        }
        return data


class Interaction(db.Model):
    IMPLICIT_RATE = 0.0

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)  # Left
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), primary_key=True)  # Right

    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    score = db.Column(db.Float, default=IMPLICIT_RATE)

    # Maps
    user = db.relationship('User', back_populates='watched_movies')
    movie = db.relationship('Movie', back_populates='spectators')

    @staticmethod
    def compute_explicit_rate(movie_id):
        rates = db.session.query(func.avg(Interaction.score).label('average_score'),
                                 func.count(Interaction.score).label('count_score'))\
            .filter(Interaction.movie_id == movie_id,
                    Interaction.score != Interaction.IMPLICIT_RATE).first()
        avg_score = rates.average_score if rates.average_score is not None else 0.0
        return avg_score, rates.count_score

    def to_dict(self, include_ts=False, explicit=True):
        data = {
            'user_id': self.user_id,
            'movie_id': self.movie_id,
        }

        if include_ts:
            data['ts'] = self.timestamp

        if explicit:
            data['rating'] = self.score

        return data

    def __repr__(self):
        return '<Interaction user={} movie={}>'.format(self.user_id, self.movie_id)
