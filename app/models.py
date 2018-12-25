from app import db
import base64
from datetime import datetime, timedelta
import os
from sqlalchemy import and_
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
        if self.partners.count() == user.partners.count() == 0:
            db.session.query(Invitation).filter_by(sender_id=self.id).delete()
            db.session.query(Invitation).filter_by(receiver_id=self.id).delete()
            db.session.query(Invitation).filter_by(sender_id=user.id).delete()
            db.session.query(Invitation).filter_by(receiver_id=user.id).delete()
            self.partners.append(user)
            user.partners.append(self)

    def unmake_partner(self, user):
        if self.is_partner(user):
            db.session.delete(user.partners)
            db.session.delete(self.partners)

    def is_partner(self, user):
        return self.partners.filter(partnerships.c.partner_b_id == user.id).count() == \
               user.partners.filter(partnerships.c.partner_b_id == self.id).count() == 1

    def invite_user(self, user):
        invitation = Invitation(sender_id=self.id,
                                receiver_id=user.id,
                                sender_username=self.username,
                                receiver_username=user.username)
        db.session.add(invitation)

    def uninvite_user(self, user):
        invitation = self.get_sent_invitation(user)
        if invitation:
            db.session.delete(invitation)

    def get_sent_invitation(self, user):
        for invitation in self.sent_invitations:
            if invitation.receiver_id == user.id:
                return invitation
        return None

    def get_received_invitation(self, user):
        for invitation in self.received_invitations:
            if invitation.sender_id == user.id:
                return invitation
        return None

    def tasks_between_dates(self, before, after):
        return Task.query.filter(and_(
            Task.user_id == self.id,
            Task.timestamp >= after,
            Task.timestamp <= before))

    def category_summaries(self, before, after):
        category_summaries = {}
        all_partners = [self] + self.partners.all()

        for i in range(0, len(all_partners)):
            partner = all_partners[i]
            partner_tasks = partner.tasks_between_dates(before, after)

            for task in partner_tasks:
                if not category_summaries.get(task.category):
                    category_summaries[task.category] = {
                        'category': task.category,
                        'total_task_count': 1,
                        'total_task_duration': task.duration,
                        'partner_task_counts': [(1 if j == i else 0) for j in range(0, len(all_partners))],
                        'partner_task_durations': [(task.duration if j == i else 0) for j in
                                                   range(0, len(all_partners))]
                    }
                else:
                    category_summaries[task.category]['total_task_count'] += 1
                    category_summaries[task.category]['total_task_duration'] += task.duration
                    category_summaries[task.category]['partner_task_counts'][i] += 1
                    category_summaries[task.category]['partner_task_durations'][i] += task.duration
                    print(category_summaries[task.category]['total_task_duration'])

        partner_usernames = [partner.username for partner in all_partners]
        category_summaries_list = [x[1] for x in category_summaries.items()]
        category_summaries_list.sort(key=lambda k: k['total_task_duration'], reverse=True)

        return {
            'partners': partner_usernames,
            'category_summaries': category_summaries_list
        }

    def category_tasks(self, category, before, after):
        all_partners = [self] + self.partners.all()

        user_id_to_name = {}
        for partner in all_partners:
            user_id_to_name[partner.id] = partner.username

        tasks = []
        for partner in all_partners:
            tasks += Task.query.filter(and_(Task.user_id == partner.id,
                                            Task.timestamp >= after,
                                            Task.timestamp <= before,
                                            Task.category == category))

        tasks.sort(key=lambda k: k.timestamp)

        task_dicts = []
        for task in tasks:
            username = user_id_to_name[task.user_id]
            task_dict = task.to_dict(username)
            task_dicts.append(task_dict)

        return {'tasks': task_dicts}


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    category = db.Column(db.String(64))
    comment = db.Column(db.String(140))
    duration = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<Task {}>'.format(self.category)

    def to_dict(self, username=None):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'category': self.category,
            'comment': self.comment,
            'duration': self.duration,
            'timestamp': self.timestamp
        }

        if username:
            data['username'] = username

        return data

    def from_dict(self, data):
        for field in ['user_id', 'category', 'comment', 'duration']:
            if field in data:
                setattr(self, field, data[field])


class Invitation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_invitations')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_invitations')
    sender_username = db.Column(db.String(64))
    receiver_username = db.Column(db.String(64))

    def __repr__(self):
        return '<Invitation {}>'.format(self.id)

    def to_dict(self):
        data = {
            'id': self.id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'sender_username': self.sender_username,
            'receiver_username': self.receiver_username
        }
        return data
