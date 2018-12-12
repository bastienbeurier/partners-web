from flask import jsonify, g
from app import db
from app.models import User
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request


@bp.route('/partnerships/<username>', methods=['POST'])
@token_auth.login_required
def create_partnership(username):
    user = User.query.filter_by(username=username).first()
    current_user = g.current_user
    if user is None:
        return bad_request('Cannot find the user you want to partner with.')
    if user == current_user:
        return bad_request('Cannot create a partnership with yourself.')
    if user.is_partner(current_user):
        return bad_request('You are already partners.')
    if current_user.partners.count():
        return bad_request('You already have a partner.')
    if user.partners.count():
        return bad_request('User already has a partner.')

    current_user.make_partner(user)
    db.session.commit()
    return '', 201


@bp.route('/partnerships/<username>', methods=['DELETE'])
@token_auth.login_required
def delete_partnership(username):
    user = User.query.filter_by(username=username).first()
    current_user = g.current_user
    if user is None:
        return bad_request('Cannot find the requested partner.')
    if not user.is_partner(current_user):
        return bad_request('You are not partners with this user.')

    current_user.unmake_partner(user)
    db.session.commit()
    return '', 201


@bp.route('/partnerships/<int:id>', methods=['GET'])
@token_auth.login_required
def get_partners(id):
    user = User.query.get_or_404(id)
    data = User.to_collection_dict(user.partners)
    return jsonify(data)
