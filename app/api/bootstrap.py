from flask import jsonify, request, g
from app import db
from app.models import User
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request

@bp.route('/bootstrap', methods=['GET'])
@token_auth.login_required
def bootstrap():
    current_user = g.current_user

    partner = current_user.partners.first()
    sent_invitation = current_user.sent_invitations.first()
    received_invitation = current_user.received_invitations.first()
    if partner:
        response = {'partner': jsonify(partner.to_dict())}
    elif sent_invitation:
        response = {'sent_invitation': jsonify(sent_invitation.to_dict())}
    elif received_invitation:
        response = {'received_invitation': jsonify(received_invitation.to_dict())}
    else:
        response = ''

    response.status_code = 200
    return response