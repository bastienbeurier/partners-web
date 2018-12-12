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
        return bad_request('cannot find the user to send an invitation to')
    if user == current_user:
        return bad_request('cannot send an invitation to yourself')
    if user.is_partner(current_user):
        return bad_request('users are already partners')

    current_user.invite_user(user)
    db.session.commit()
    return '', 201

@bp.route('/invitations/<username>', methods=['DELETE'])
@token_auth.login_required
def delete_invitation(username):
    user = User.query.filter_by(username=username).first()
    current_user = g.current_user
    if user is None:
        return bad_request('cannot find the user to uninvite')
    if user == current_user:
        return bad_request('cannot uninvite yourself')
    if user.is_partner(current_user):
        return bad_request('users are already partners')

    current_user.uninvite_user(user)
    db.session.commit()
    return '', 201