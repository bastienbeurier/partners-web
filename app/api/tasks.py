from flask import jsonify, request
from app import db
from app.models import User, Task
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request

@bp.route('/tasks', methods=['POST'])
@token_auth.login_required
def create_user():
    data = request.get_json() or {}
    if 'category' not in data:
        return bad_request('must include category field')
    task = Task(user_id=g.current_user.id)
    task.from_dict(data)
    db.session.add(task)
    db.session.commit()
    response = jsonify(task.to_dict())
    response.status_code = 201
    return response