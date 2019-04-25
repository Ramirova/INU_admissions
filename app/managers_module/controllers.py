from flask import (
    Blueprint,
    request,
    Response,
    jsonify,
    make_response
)

from flask_jwt_extended import jwt_required
from app.candidates_module.models import Candidate, TestsStates
from app.candidates_module.controllers import get_token_info, send_message
from app.staff_module.models import Staff_member
from .models import Interview, db
from sqlalchemy import func
module = Blueprint('managers', __name__, url_prefix='/api/managers')


@module.route('/updateStatus', methods=['POST'])
@jwt_required
def update_candidate_status():
    login, role = get_token_info(request)
    if login == "User not authorized":
        return Response("Token expired", status=401, mimetype='application/json')
    if role == 'manager':
        candidate = Candidate.query.get(request.get_json().get('login'))
        status = request.get_json().get('status')
        if candidate:
            candidate.status = status
            db.session.commit()

            if status == 'PASSING_TESTS':
                test_states = TestsStates.query.filter_by(candidate=candidate.login).all()
                for test_state in test_states:
                    test_state.permission = "granted"
                    db.session.commit()

            return Response("Success", status=200, mimetype='application/json')
        return Response("", status=401, mimetype='application/json')
    else:
        return Response("You do not have access rights", status=401, mimetype='application/json')


@module.route('/users', methods=["GET"])
@jwt_required
def get_users():
    login, user_role = get_token_info(request)
    if login == "User not authorized":
        return Response("Token expired", status=401, mimetype='application/json')
    if user_role == 'manager':
        role = request.args.get('role')
        result_data = []
        if role == 'candidate':
            candidates = Candidate.query.all()
            if request.args.get('status'):
                candidates = Candidate.query.filter_by(state=request.args.get('status'))
            for user in candidates:
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
    else:
        return Response("You do not have access rights", status=401, mimetype='application/json')


@module.route('/interview', methods=["POST"])
@jwt_required
def create_interview():
    login, user_role = get_token_info(request)
    if login == "User not authorized":
        return Response("Token expired", status=401, mimetype='application/json')
    if user_role == 'manager':
        candidate = request.get_json().get('candidate')
        staff_member = request.get_json().get('staff_member')
        date = request.get_json().get('date')

        max_inerview_id = db.session.query(func.max(Interview.id)).scalar()
        max_id = 0
        if max_inerview_id:
            max_id = int(max_inerview_id) + 1
        interview = Interview(candidate, staff_member, date, max_id+1)
        candidate_user = Candidate.query.get(candidate)
        candidate_user.state = "INTERVIEW_ASSIGNED"
        db.session.add(interview)
        db.session.commit()
        body = "You have been assigned for the interview. It will be on " + date
        send_message(candidate, "You have been assigned for the interview.", body)
        return make_response("Success"), 200
    else:
        return Response("You do not have access rights", status=401, mimetype='application/json')
