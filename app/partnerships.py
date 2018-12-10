from app import app
from app import db
from app.auth import token_auth
from app.errors import bad_request
from app.models import User
from flask import jsonify
from flask import request

@app.route('/partnerships/<username>', methods=['POST'])
@token_auth.login_required
def create_partnership(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        return bad_request('cannot find the user to create a partnership with')
    if user == current_user:
        return bad_request('cannot create a partnership with yourself')
    if user.is_partner(current_user):
        return bad_request('users are already partners')
    current_user.make_partner(user)
    user.make_partner(current_user)
    db.session.commit()
    return '', 201

@app.route('/partnerships/<username>', methods=['DELETE'])
@token_auth.login_required
def delete_partnership(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        return bad_request('cannot find the partner')
    if user == current_user:
        return bad_request('cannot unmake partnership with yourself')
    if not user.is_partner(current_user):
        return bad_request('users are not partners')
    current_user.unmake_partner(user)
    user.unmake_partner(current_user)
    db.session.commit()
    return '', 201
