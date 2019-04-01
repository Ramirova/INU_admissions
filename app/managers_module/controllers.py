from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    abort,
    redirect,
    url_for,
    current_app,
    Response,
    jsonify,
    make_response
)

import json
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    jwt_refresh_token_required,
    get_jwt_identity,
    get_raw_jwt
)

from app.candidates_module.models import Candidate
from app.staff_module.models import Staff_member
from .models import Manager, db
from sqlalchemy.exc import SQLAlchemyError

module = Blueprint('managers', __name__, url_prefix='/managers')


# @module.route('/login', methods=["POST"])
# def auth():
#     candidate = Manager.query.get(request.get_json().get('login'))
#     auth_token = create_access_token(identity=candidate.login)
#     if auth_token:
#         response = {
#             'token': auth_token,
#             'refresh_token': create_refresh_token(identity=candidate.login)
#         }
#         return make_response(jsonify(response)), 200
#     return Response("", status=401, mimetype='application/json')
#
#
# # The jwt_refresh_token_required decorator insures a valid refresh
# # token is present in the request before calling this endpoint. We
# # can use the get_jwt_identity() function to get the identity of
# # the refresh token, and use the create_access_token() function again
# # to make a new access token for this identity.
# @module.route('/refresh', methods=['POST'])
# @jwt_refresh_token_required
# def refresh():
#     current_user = get_jwt_identity()
#     ret = {
#         'access_token': create_access_token(identity=current_user)
#     }
#     return jsonify(ret), 200

@module.route('/upload', methods=['POST'])
@jwt_required
def update_candidate_status():
    candidate = Candidate.query.get(request.get_json().get('login'))
    status = request.get_json().get('status')
    if candidate:
        candidate.status = status
        db.session.commit()
        return Response("Success", status=200, mimetype='application/json')
    return Response("", status=201, mimetype='application/json')


@module.route('/profile', methods=["GET"])
@jwt_required
def profile_info():
    candidate = Manager.query.get(request.args.get('login'))
    response = {
        'name': candidate.name,
        'surname': candidate.surname,
        'second_name': candidate.second_name
    }
    return make_response(jsonify(response)), 200


@module.route('/users', methods=["GET"])
@jwt_required
def get_users():
    role = request.args.get('role')
    result_data = []
    if role == 'candidate':
        for user in Candidate.query.all():
            result_data.append({
                'login': user.login,
                'name': user.name,
                'surname': user.surname,
                'second_name': user.second_name,
                'date_of_birth': str(user.date_of_birth),
                'status': user.state,
                'nationality': user.nationality
            })
    elif role == 'staff_member':
        for user in Staff_member.query.all():
            result_data.append({
                'login': user.login,
                'name': user.name,
                'surname': user.surname,
                'second_name': user.second_name,
            })
    return make_response(jsonify(result_data)), 200



