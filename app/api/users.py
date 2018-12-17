from flask import jsonify, request
from app import db
from app.models import User
from app.api import bp
from app.api.errors import bad_request


@bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json() or {}

    if 'username' not in data or 'email' not in data or 'password' not in data:
        return bad_request('Signup request must include username, email and password.')
    if User.query.filter_by(username=data['username']).first():
        return bad_request('Username is already taken.')
    if User.query.filter_by(email=data['email']).first():
        return bad_request('Email is already taken.')

    user = User()
    user.from_dict(data, new_user=True)
    db.session.add(user)
    db.session.commit()
    response = jsonify(user.to_dict())
    response.status_code = 201
    return response

@bp.route('/', methods=['GET'])
def index():
    response = jsonify({"message": "success"})
    response.status_code = 200
    return response