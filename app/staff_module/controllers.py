from flask import (
    Blueprint,
    request,
    Response,
    jsonify,
    make_response
)

from flask_jwt_extended import jwt_required

from app.managers_module.models import Interview
from app.candidates_module.models import Candidate
from app.common.controllers import get_profile_info
from .models import Staff_member, db
from app.common.models import User
from app.candidates_module.controllers import get_token_info
module = Blueprint('staff', __name__, url_prefix='/api/staff')


@module.route('/profile', methods=["GET"])
@jwt_required
def get_profile():
    """
        Method returns profile information for a requested user
        :return: 200 and json with profile information if everything is ok; 401 if user do not have access rights
    """
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
    """
    Method for getting a list of interviews assigned to staff member
    :return: list of interviews assigned to staff member
    """
    login, user_role = get_token_info(request)
    if login == "User not authorized":
        return Response("Token expired", status=401, mimetype='application/json')
    if user_role == 'staff_member':
        interviews = Interview.query.filter_by(interviewer=request.args.get('login')).all()
        response_data = []
        for interview in interviews:
            candidate = User.query.get(interview.student)
            interviewer = User.query.get(interview.interviewer)
            response_data.append({
                'student': get_profile_info(candidate),
                'interviewer': get_profile_info(interviewer),
                'date': interview.date,
                'new': interview.new,
                'student_login': candidate.login
            })
            interview.new = 'old'
            db.session.commit()
        return make_response(jsonify(response_data)), 200
    else:
        return Response("You do not have access rights, you are: " + user_role + ", but should be staff member",
                        status=401, mimetype='application/json')


@module.route('/grade', methods=["POST"])
@jwt_required
def grade_student():
    """
    Posting grade for a given student
    :return: 200 if grade is posted; 401 if user do not have access rights
    """
    login, user_role = get_token_info(request)
    if login == "User not authorized":
        return Response("Token expired", status=401, mimetype='application/json')
    if user_role == 'staff_member':
        candidate = Candidate.query.filter_by(login=request.get_json().get('student_login')).first()
        candidate.grade = request.get_json().get('grade')
        candidate.state = "GRADED"
        db.session.commit()
        return Response("Success", status=200, mimetype='application/json')
    else:
        return Response("You do not have access rights", status=401, mimetype='application/json')


@module.route('/newInterviews', methods=["GET"])
@jwt_required
def get_new_interviews():
    """
    Method for getting a list of new interviews assigned to staff member
    :return: list of new interviews assigned to staff member
    """
    login, user_role = get_token_info(request)
    if login == "User not authorized":
        return Response("Token expired", status=401, mimetype='application/json')
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
