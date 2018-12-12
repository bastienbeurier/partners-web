from flask import jsonify, request, g
from app import db
from app.models import Task
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request
from datetime import datetime

@bp.route('/tasks', methods=['POST'])
@token_auth.login_required
def create_task():
    data = request.get_json() or {}
    if 'category' not in data or 'duration' not in data:
        return bad_request('Task must include category and duration fields.')
    task = Task(user_id=g.current_user.id)
    task.from_dict(data)
    db.session.add(task)
    db.session.commit()
    response = jsonify(task.to_dict())
    response.status_code = 201
    return response

@bp.route('/tasks', methods=['GET'])
@token_auth.login_required
def get_task():
    before = request.args.get('before', default = None, type = toDate)
    after = request.args.get('after', default = None, type = toDate)

    if not before or not after:
        return bad_request('Request must include valid before and after date parameters.')

    response = jsonify(g.current_user.category_summaries(before, after))
    response.status_code = 200
    return response

def toDate(dateString): 
    return datetime.strptime(dateString, "%Y-%m-%d-%H-%M")

