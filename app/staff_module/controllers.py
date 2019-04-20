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

from app.managers_module.models import Interview
from app.candidates_module.models import Candidate
from .models import Staff_member, db
from app.candidates_module.controllers import get_token_info
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
module = Blueprint('staff', __name__, url_prefix='/api/staff')


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
def get_profile_info():
    user = Staff_member.query.get(request.args.get('login'))
    response = {
        'name': user.name,
        'surname': user.surname,
        'second_name': user.second_name
    }
    return make_response(jsonify(response)), 200


@module.route('/interviews', methods=["GET"])
@jwt_required
def get_interviews():
    login, user_role = get_token_info(request)
    if user_role == 'staff_member':
        interviews = Interview.query.filter_by(interviewer=request.get_json().get('login')).all()
        response_data = []
        for interview in interviews:
            response_data.append({
                'student': interview.student,
                'interviewer': interview.interviewer,
                'date': interview.date
            })
        return make_response(jsonify(response_data)), 200
    else:
        return Response("You do not have access rights", status=401, mimetype='application/json')


@module.route('/grade', methods=["POST"])
@jwt_required
def grade_student():
    login, user_role = get_token_info(request)
    if user_role == 'staff_member':
        candidate = Candidate.query.filter_by(login=request.get_json().get('student_login')).first()
        candidate.grade = request.get_json().get('grade')
        db.session.commit()
        return Response("Success", status=200, mimetype='application/json')
    else:
        return Response("You do not have access rights", status=401, mimetype='application/json')


@module.route('/newInterviews', methods=["GET"])
@jwt_required
def get_new_interviews():
    login, user_role = get_token_info(request)
    if user_role == 'staff_member':
        interviews = Interview.query.filter_by(interviewer=request.get_json().get('login')).all()
        response_data = []
        for interview in interviews:
            if interview.new == 'new':
                response_data.append({
                    'student': interview.student,
                    'interviewer': interview.interviewer,
                    'date': interview.date
                })
                interview.new = 'old'
        db.session.commit()
        return make_response(jsonify(response_data)), 200
    else:
        return Response("You do not have access rights", status=401, mimetype='application/json')
