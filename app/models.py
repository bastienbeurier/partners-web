from app import db
import base64
from datetime import datetime, timedelta
from flask import url_for
import os
from werkzeug.security import generate_password_hash, check_password_hash

partnerships = db.Table('partnerships',
    db.Column('partner_a_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('partner_b_id', db.Integer, db.ForeignKey('user.id'))
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    tasks = db.relationship('Task', backref='author', lazy='dynamic')
    token = db.Column(db.String(32), index=True, unique=True)
    token_expiration = db.Column(db.DateTime)
    partners = db.relationship(
        'User', secondary=partnerships,
        primaryjoin=(partnerships.c.partner_a_id == id),
        secondaryjoin=(partnerships.c.partner_b_id == id), lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self, include_email=False):
        data = {
            'id': self.id,
            'username': self.username
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

    @staticmethod
    def to_collection_dict(items):
        data = {
            'items': [item.to_dict() for item in items]
        }
        return data

    def get_token(self, expires_in=365):
        now = datetime.utcnow()
        if self.token and self.token_expiration > now + timedelta(days=7):
            return self.token
        self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
        self.token_expiration = now + timedelta(days=expires_in)
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

    def make_partner(self, user):
        if not self.is_partner(user):
            self.partners.append(user)

    def unmake_partner(self, user):
        if self.is_partner(user):
            self.partners.remove(user)

    def is_partner(self, user):
        return self.partners.filter(
            partnerships.c.partner_b_id == user.id).count() > 0

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(64))
    comment = db.Column(db.String(140))
    duration = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Task {}>'.format(self.category)
