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

from .models import User, Notification, Token, db
from app.candidates_module.models import Candidate
from app.staff_module.models import Staff_member
from app.managers_module.models import Manager
from app.candidates_module.controllers import get_token_info, send_message
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
            if db.session.query(Token).filter_by(login=user.login).count():
                token = Token.query.get(user.login)
                response = {
                    'token': token.token,
                    'refresh_token': create_refresh_token(identity=user.login),
                    'role': user.role
                }
                return make_response(jsonify(response)), 200
            else:
                auth_token = create_access_token(identity=user.login)
                if auth_token:
                    response = {
                        'token': auth_token,
                        'refresh_token': create_refresh_token(identity=user.login),
                        'role': user.role
                    }
                    token = Token(user.login, auth_token)
                    db.session.add(token)
                    db.session.commit()
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
    login, role = get_token_info(request)
    if login == "User not authorized":
        return Response("Token expired", status=401, mimetype='application/json')
    user = User.query.get(request.args.get('login'))
    response_data = get_profile_info(user)
    if response_data and login == request.args.get('login'):
        return make_response(jsonify(response_data)), 200
    else:
        return Response("You do not have access rights", status=401, mimetype='application/json')


def get_profile_info(user):
    if user.role == 'candidate':
        candidate = Candidate.query.get(user.login)
        response_data = {
            'name': candidate.name,
            'surname': candidate.surname,
            'second_name': candidate.second_name,
            'role': 'candidate',
            'status': candidate.state,
            'progress': candidate_progress[candidate.state],
            'photo': "app/user_files/sample_photo.png"
        }
        return response_data
    if user.role == 'staff_member':
        staff = Staff_member.query.get(user.login)
        response_data = {
            'name': staff.name,
            'surname': staff.surname,
            'second_name': staff.second_name,
            'role': 'staff_member'
        }
        return response_data
    if user.role == 'manager':
        manager = Manager.query.get(user.login)
        response_data = {
            'name': manager.name,
            'surname': manager.surname,
            'second_name': manager.second_name,
            'role': 'manager'
        }
        return response_data
    return None


@module.route('/changeProfile', methods=["POST"])
@jwt_required
def change_profile_info():
    real_login, role = get_token_info(request)
    if real_login == "User not authorized":
        return Response("Token expired", status=401, mimetype='application/json')
    login = request.args.get('login')
    user = User.query.get(login)
    if user.role == 'candidate' and real_login == request.args.get('login'):
        candidate = Candidate.query.get(login)
        candidate.name = request.get_json().get('name')
        candidate.surname = request.get_json().get('surname')
        candidate.state = request.get_json().get('status')
        db.session.commit()
        return Response("Success", status=200, mimetype='application/json')
    if user.role == 'staff_member' and real_login == request.args.get('login'):
        staff = Staff_member.query.get(login)
        staff.name = request.get_json().get('name')
        staff.surname = request.get_json().get('surname')
        db.session.commit()
        return Response("Success", status=200, mimetype='application/json')
    if user.role == 'manager' and real_login == request.args.get('login'):
        manager = Manager.query.get(login)
        manager.name = request.get_json().get('name')
        manager.surname = request.get_json().get('surname')
        db.session.commit()
        return Response("Success", status=200, mimetype='application/json')
    return Response("You do not have access rights", status=401, mimetype='application/json')

@module.route('/getNotifications', methods=["GET"])
@jwt_required
def get_notifications():
    real_login, role = get_token_info(request)
    if real_login == "User not authorized":
        return Response("Token expired", status=401, mimetype='application/json')
    if real_login == request.args.get('login'):
        notifications = Notification.query.filter_by(receiver=request.args.get('login')).all()
        response_data = []
        for notification in notifications:
            response_data.append({
                'date': notification.date,
                'body': notification.interviewer.body,
                'status': notification.status
            })
        return make_response(jsonify(response_data)), 200
    else:
        return Response("You do not have access rights", status=401, mimetype='application/json')


@module.route('/download', methods=['GET'])
@jwt_required
def download():
    real_login, role = get_token_info(request)
    if real_login == "User not authorized":
        return Response("Token expired", status=401, mimetype='application/json')
    if real_login == request.args.get('login'):
        login = request.args.get('login')
        filename = request.args.get('filename')
        uploads = "app/user_files/" + login
        return send_from_directory(directory=uploads, filename=filename)
    else:
        return Response("You do not have access rights", status=401, mimetype='application/json')
