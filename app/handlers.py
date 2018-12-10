from flask import request
from app import db
from app.errors import error_response

@app.app_errorhandler(404)
def not_found_error(error):
    return error_response(404)

@app.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return error_response(500)