import base64
import os
from datetime import datetime, timedelta

from flask import url_for
from flask_login import UserMixin
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    firstName = db.Column(db.String(64), index=True, unique=True)
    lastName = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    watched_movies = db.relationship('Interaction', back_populates='user')
    token = db.Column(db.String(32), index=True, unique=True)
    token_expiration = db.Column(db.DateTime)
    
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

    def has_rated(self, movie):
        return Interaction.query.filter(
            Interaction.user_id == self.id,
            Interaction.movie_id == movie.id,
            Interaction.score != Interaction.IMPLICIT_RATE).count() > 0

    def get_token(self, expires_in=3600):
        now = datetime.utcnow()
        if self.token and self.token_expiration > now + timedelta(seconds=60):
            return self.token
        self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token

    def revoke_token(self):
        self.token_expiration = datetime.utcnow() - timedelta(seconds=1)

    @staticmethod
    def check_token(token):
        user = User.query.filter_by(token=token).first()
        if user is None or user.token_expiration < datetime.utcnow():
            return None
        return user

    def to_dict(self, include_email=False):
        data = {
            'id': self.id,
            'username': self.username,
            'firstName': self.firstName,
            'lastName': self.lastName,
            '_links': {
                'self': url_for('api.get_user', id=self.id, _external=True),
                'watched_movies': url_for('api.get_watched_movies', id=self.id, _external=True),
                'recommended_movies': url_for('api.get_recommended_movies', id=self.id, _external=True)
            }
        }
        if include_email:
            data['email'] = self.email
        return data

    def from_dict(self, data, new_user=False):
        fields = ['username', 'email']
        if new_user:
            fields.append('firstName')
            fields.append('lastName')
        for field in fields:
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])


# Helper for LoginManager to load users from model
@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class PaginatedAPIMixin(object):
    @staticmethod
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        resources = query.paginate(page, per_page, False)
        data = {
            'items': [item.to_dict() for item in resources.items],
            '_meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': resources.pages,
                'total_items': resources.total
            },
            '_links': {
                'self': url_for(endpoint, page=page, per_page=per_page,
                                **kwargs),
                'next': url_for(endpoint, page=page + 1, per_page=per_page,
                                **kwargs) if resources.has_next else None,
                'prev': url_for(endpoint, page=page - 1, per_page=per_page,
                                **kwargs) if resources.has_prev else None
            }
        }
        return data


class Movie(PaginatedAPIMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    imdb_id = db.Column(db.Integer, default=0)
    tmdb_id = db.Column(db.Integer, default=0)
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
            'imdbId': self.imdb_id,
            'tmdbId': self.tmdb_id,
            'title': self.title,
            'description': self.description,
            'rating': {
                'score': score,
                'support': support
            },
            '_links': {
                'self': url_for('api.get_movie', id=self.id, _external=True),
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
