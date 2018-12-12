from flask import g
from app import db
from app.models import User
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request


@bp.route('/invitations/<username>', methods=['POST'])
@token_auth.login_required
def create_invitation(username):
    user = User.query.filter_by(username=username).first()
    current_user = g.current_user
    if user is None:
        return bad_request('Cannot find the user to send an invitation to.')
    if user == current_user:
        return bad_request('Cannot send an invitation to yourself.')
    if user.is_partner(current_user):
        return bad_request('You are already partners with this user.')
    if current_user.partners.count():
        return bad_request('You already have a partner.')
    if user.partners.count():
        return bad_request('This user already has a partner.')
    if current_user.sent_invitations.count():
        return bad_request('You have a sent invitation pending.')
    if current_user.received_invitations.count():
        return bad_request('You have a received invitation pending.')
    if user.sent_invitations.count():
        return bad_request('Invited user has a sent invitation pending.')
    if user.received_invitations.count():
        return bad_request('Invited user has a received invitation pending.')

    current_user.invite_user(user)
    db.session.commit()
    return '', 201


@bp.route('/sent_invitations/<username>', methods=['DELETE'])
@token_auth.login_required
def delete_sent_invitation(username):
    user = User.query.filter_by(username=username).first()
    current_user = g.current_user
    if user is None:
        return bad_request('Cannot find the user to you want to uninvite.')
    if not current_user.get_sent_invitation(user):
        return bad_request('You did not invite this user.')

    current_user.uninvite_user(user)
    db.session.commit()
    return '', 201


@bp.route('/received_invitations/<username>', methods=['DELETE'])
@token_auth.login_required
def delete_received_invitation(username):
    user = User.query.filter_by(username=username).first()
    current_user = g.current_user
    if user is None:
        return bad_request('Cannot find the user who invited you.')
    if not current_user.get_received_invitation(user):
        return bad_request('You did not receive an invitation from this user.')

    user.uninvite_user(current_user)
    db.session.commit()
    return '', 201
