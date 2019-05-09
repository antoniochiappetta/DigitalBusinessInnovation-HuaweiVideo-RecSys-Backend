from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import url_for
from app import db, login


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
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
        if not self.has_watched(movie):
            i = Interaction()
            i.movie = movie
            self.watched_movies.append(i)

    def un_watch(self, movie):
        if self.has_watched(movie):
            i = Interaction()
            i.movie = movie
            self.watched_movies.remove(i)

    def has_watched(self, movie):
        return Interaction.query.filter(
            Interaction.user_id == self.id,
            Interaction.movie_id == movie.id).count() > 0

    def to_dict(self, include_email=False):
        data = {
            'id': self.id,
            'username': self.username,
            '_links': {
                'self': url_for('api.get_user', id=self.id),
                'watched_movies': url_for('api.watched_movies', id=self.id)
            }
        }
        if include_email:
            data['email'] = self.email
        return data

    def from_dict(self, data, new_user=False):
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
    link = db.Column(db.String(64))
    spectators = db.relationship('Interaction', back_populates='movie')

    def __repr__(self):
        return '<Movie {}>'.format(self.title)

    def to_dict(self):
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            '_links': {
                'self': url_for('api.get_movie', id=self.id),
                'trailer': self.link
            }
        }
        return data


class Interaction(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)  # Left
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), primary_key=True)  # Right
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    # Maps
    user = db.relationship('User', back_populates='watched_movies')
    movie = db.relationship('Movie', back_populates='spectators')

    def __repr__(self):
        return '<Interaction user={} movie={}>'.format(self.user_id, self.movie_id)
