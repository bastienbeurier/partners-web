from app import app
from app import db
from app.auth import basic_auth, token_auth
from app.errors import bad_request
from app.models import User
from flask import jsonify
from flask import request

@app.route('/users/<int:id>', methods=['GET'])
@token_auth.login_required
def get_user(id):
    return jsonify(User.query.get_or_404(id).to_dict())

@app.route('/users/<int:id>/partners', methods=['GET'])
@token_auth.login_required
def get_partners(id):
	pass
    # user = User.query.get_or_404(id)
    # data = User.to_collection_dict(user.followers)
    # return jsonify(data)

@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json() or {}
    if 'username' not in data or 'email' not in data or 'password' not in data:
        return bad_request('must include username, email and password fields')
    if User.query.filter_by(username=data['username']).first():
        return bad_request('please use a different username')
    if User.query.filter_by(email=data['email']).first():
        return bad_request('please use a different email address')
    user = User()
    user.from_dict(data, new_user=True)
    db.session.add(user)
    db.session.commit()
    response = jsonify(user.to_dict())
    response.status_code = 201
    return response