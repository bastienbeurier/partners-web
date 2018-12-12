from flask import jsonify, request
from app import db
from app.models import User
from app.api import bp
from app.api.errors import bad_request


@bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json() or {}

    if 'username' not in data or 'email' not in data or 'password' not in data:
        return bad_request('Request must include username, email and password fields.')
    if User.query.filter_by(username=data['username']).first():
        return bad_request('Please use a different username, this one is already taken.')
    if User.query.filter_by(email=data['email']).first():
        return bad_request('Please use a different email address, this one is already taken.')

    user = User()
    user.from_dict(data, new_user=True)
    db.session.add(user)
    db.session.commit()
    response = jsonify(user.to_dict())
    response.status_code = 201
    return response
