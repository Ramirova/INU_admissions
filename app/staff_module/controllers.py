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

from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    jwt_refresh_token_required,
    get_jwt_identity,
    get_raw_jwt
)

from .models import Staff_member, db
from sqlalchemy.exc import SQLAlchemyError

module = Blueprint('staff', __name__, url_prefix='/staff')


@module.route('/login', methods=["POST"])
def auth():
    user = Staff_member.query.get(request.get_json().get('login'))
    auth_token = create_access_token(identity=user.login)
    if auth_token:
        response = {
            'token': auth_token,
            'refresh_token': create_refresh_token(identity=user.login)
        }
        return make_response(jsonify(response)), 200
    return Response("", status=401, mimetype='application/json')


# The jwt_refresh_token_required decorator insures a valid refresh
# token is present in the request before calling this endpoint. We
# can use the get_jwt_identity() function to get the identity of
# the refresh token, and use the create_access_token() function again
# to make a new access token for this identity.
@module.route('/refresh', methods=['POST'])
@jwt_refresh_token_required
def refresh():
    current_user = get_jwt_identity()
    ret = {
        'access_token': create_access_token(identity=current_user)
    }
    return jsonify(ret), 200


@module.route('/profile', methods=["GET"])
@jwt_required
def profile_info():
    user = Staff_member.query.get(request.args.get('login'))
    response = {
        'name': user.name,
        'surname': user.surname,
        'second_name': user.second_name
    }
    return make_response(jsonify(response)), 200