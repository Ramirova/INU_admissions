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
    make_response,
    send_from_directory
)

from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    jwt_refresh_token_required,
    get_jwt_identity,
    get_raw_jwt
)

from .models import User, Notification, db
from app.candidates_module.models import Candidate
from app.staff_module.models import Staff_member
from app.managers_module.models import Manager
from sqlalchemy.exc import SQLAlchemyError

module = Blueprint('api', __name__, url_prefix='/api')

candidate_progress = {
    'GRADED': 100,
    'INTERVIEWED': 90,
    'INTERVIEW_ASSIGNED': 70,
    'PASSED_TESTS': 50,
    'PASSING_TESTS': 30,
    'REGISTERED': 10
}

@module.route('/login', methods=["POST"])
def auth():
    user = User.query.get(request.get_json().get('login'))
    if user:
        if user.password == request.get_json().get('password'):
            auth_token = create_access_token(identity=user.login)
            if auth_token:
                response = {
                    'token': auth_token,
                    'refresh_token': create_refresh_token(identity=user.login),
                    'role': user.role
                }
                return make_response(jsonify(response)), 200
            return Response("", status=401, mimetype='application/json')
        else:
            return Response("Wrong password", status=401, mimetype='application/json')
    else:
        return Response("Wrong login", status=401, mimetype='application/json')


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
    user = User.query.get(request.args.get('login'))
    response_data = []
    if user.role == 'candidate':
        candidate = Candidate.query.get(request.args.get('login'))
        response_data = {
            'name': candidate.name,
            'surname': candidate.surname,
            'second_name': candidate.second_name,
            'role': 'candidate',
            'status': candidate.state,
            'progress': candidate_progress[candidate.state]
        }
    if user.role == 'staff_member':
        staff = Staff_member.query.get(request.args.get('login'))
        response_data = {
            'name': staff.name,
            'surname': staff.surname,
            'second_name': staff.second_name,
            'role': 'staff_member'
        }
    if user.role == 'manager':
        manager = Manager.query.get(request.args.get('login'))
        response_data = {
            'name': manager.name,
            'surname': manager.surname,
            'second_name': manager.second_name,
            'role': 'manager'
        }
    return make_response(jsonify(response_data)), 200

@module.route('/changeProfile', methods=["POST"])
@jwt_required
def change_profile_info():
    login = request.get_json().get('login')
    user = User.query.get(login)
    response_data = []
    if user.role == 'candidate':
        candidate = Candidate.query.get(login)
        candidate.name = request.get_json().get('name')
        candidate.surname = request.get_json().get('surname')
        candidate.state = request.get_json().get('status')
    if user.role == 'staff_member':
        staff = Staff_member.query.get(login)
        staff.name = request.get_json().get('name')
        staff.surname = request.get_json().get('surname')
    if user.role == 'manager':
        manager = Manager.query.get(login)
        manager.name = request.get_json().get('name')
        manager.surname = request.get_json().get('surname')
    db.session.commit()
    return make_response(jsonify(response_data)), 200


@module.route('/getNotifications', methods=["GET"])
@jwt_required
def get_notifications():
    notifications = Notification.query.filter_by(interviewer=request.args.get('login')).all()
    response_data = []
    for notification in notifications:
        response_data.append({
            'date': notification.date,
            'body': notification.interviewer.body,
            'status': notification.status
        })
    return make_response(jsonify(response_data)), 200


@module.route('/download', methods=['GET'])
@jwt_required
def download():
    login = request.args.get('login')
    filename = request.args.get('filename')
    uploads = "app/user_files/" + login
    return send_from_directory(directory=uploads, filename=filename)

