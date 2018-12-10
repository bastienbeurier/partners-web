from flask import jsonify, request
from app import db
from app.models import User
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request

@bp.route('/partnerships/<username>', methods=['POST'])
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

@bp.route('/partnerships/<username>', methods=['DELETE'])
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

@app.route('/partnerships/<int:id>', methods=['GET'])
@token_auth.login_required
def get_partners(id):
    user = User.query.get_or_404(id)
    data = User.to_collection_dict(user.partners)
    return jsonify(data)
