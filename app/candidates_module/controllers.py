from flask import (
    Blueprint,
    request,
    Response,
    jsonify,
    make_response
)
import os
from app import app
from werkzeug.utils import secure_filename
from flask_mail import Message
from flask_jwt_extended import jwt_required
from threading import Thread
from app.common.models import User, Token
from app.managers_module.models import Interview
from .models import Candidate, Tests, TestsStates, db
from sqlalchemy import func
from app.email import mail

module = Blueprint('candidates', __name__, url_prefix='/api/candidates')

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}


@module.route('/upload', methods=['POST'])
@jwt_required
def upload_file():
    """
    This methods allows users upload file. They need to specify in JSON login and file name
    :return: 200 if everything is OK and other standard status codes otherwise
    """
    candidate = Candidate.query.get(request.get_json().get('login'))
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join("app/user_files/", candidate.login, filename))
        return Response("", status=200, mimetype='application/json')
    else:
        return Response("Invalid filename", status=401, mimetype='application/json')


def allowed_file(filename):
    """
    Checks whether filename is legal
    :param filename: name of file than needs to be checked
    :return: true if file name is legal and false otherwise
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@module.route('/register', methods=['POST'])
def register():
    """
    POST method which allows to register new user. In JSON should be specified all the information about new user:
    login, password, name, surname, second_name, date_of_birth, nationality, skype, contact_number, program
    :return: 200 if user registered; 401 if user exists and other standard status codes otherwise
    """
    login = request.get_json().get('login')
    password = request.get_json().get('password')
    name = request.get_json().get('name')
    surname = request.get_json().get('surname')
    second_name = request.get_json().get('second_name')
    date_of_birth = request.get_json().get('date_of_birth')
    nationality = request.get_json().get('nationality')
    skype = request.get_json().get('skype')
    contact_number = request.get_json().get('contact_number')
    program = request.get_json().get('program')
    candidate = Candidate.query.get(request.get_json().get('login'))
    if not candidate:
        try:
            os.mkdir("app/user_files/" + login, 0o755)
        except OSError:
            print("Creation of the directory %s failed" % "app/user_files/" + login)

        new_user = User(login, password, 'candidate')
        db.session.add(new_user)
        db.session.commit()
        new_candidate = Candidate(login, password, name, surname, second_name, date_of_birth, nationality, skype,
                                  contact_number, program)
        db.session.add(new_candidate)
        db.session.commit()
        tests = Tests.query.filter_by(program=program).all()
        max_id = int(db.session.query(func.max(TestsStates.id)).scalar())
        if not max_id:
            max_id = 0
        for test in tests:
            max_id += 1
            new_test_progress = TestsStates(login, test.name, max_id)
            db.session.add(new_test_progress)

        db.session.commit()
        return Response("Success", status=200, mimetype='application/json')
    return Response("User with given login already exists", status=401, mimetype='application/json')


@module.route('/profileDetails', methods=['POST'])
@jwt_required
def profile_details():
    """
    POST methods allows users to change profile details
    :return: 200 if everything is ok; 401 if user with given login exists and 402 if user do not have access rights
    """
    login, role = get_token_info(request)
    if role != 'candidate' or login == request.args.get('login'):
        contact_number = request.get_json().get('telephone')
        program = request.get_json().get('program')
        nationality = request.get_json().get('country')
        skype = request.get_json().get('skype')

        candidate = Candidate.query.get(request.args.get('login'))
        if candidate:
            candidate.nationality = nationality
            candidate.skype = skype
            candidate.program = program
            candidate.phone_number = contact_number
            db.session.commit()
            return Response("Success", status=200, mimetype='application/json')
        return Response("User with given login does not exist", status=401, mimetype='application/json')
    else:
        return Response("You do not have access rights", status=402, mimetype='application/json')


@module.route('/profile', methods=["GET"])
@jwt_required
def profile_info():
    """
    Method returns profile information for a requested user
    :return: 200 and json with profile information if everything is ok; 401 if user do not have access rights
    """
    login, role = get_token_info(request)
    if role != 'candidate' or login == request.args.get('login'):
        candidate = Candidate.query.get(request.args.get('login'))
        response = {
            'telephone': candidate.phone_number,
            'email': candidate.login,
            'program': candidate.program,
            'country': candidate.nationality,
            'skype': candidate.skype,
        }
        return make_response(jsonify(response)), 200
    else:
        return Response("You do not have access rights", status=401, mimetype='application/json')


@module.route('/interviews', methods=["GET"])
@jwt_required
def get_interviews():
    """
    Method returns interviews assigned for a perticular user (candidate or staff meber)
    :return: 200 and json with interview if everything is ok; 401 if user do not have access rights
    """
    login, role = get_token_info(request)
    if role != 'candidate' or login == request.args.get('login'):
        interview = Interview.query.filter_by(student=request.args.get('login')).first()
        if interview:
            response_data = {
                'student': interview.student,
                'interviewer': interview.interviewer,
                'date': interview.date
            }
            return make_response(jsonify(response_data)), 200
        else:
            return make_response(jsonify([])), 200
    else:
        return Response("You do not have access rights", status=401, mimetype='application/json')


@module.route('/testInfo', methods=["GET"])
@jwt_required
def get_tests():
    """
    Method for getting statuses of test assigned to candidate
    :return: statuses of test assigned to candidate
    """
    login, role = get_token_info(request)
    if role != 'candidate' or login == request.args.get('login'):
        tests = TestsStates.query.filter_by(candidate=request.args.get('login')).all()
        response_data = []
        for test in tests:
            response_data.append({
                'test_name': test.test,
                'status': test.status,
                'result': test.result
            })
        return make_response(jsonify(response_data)), 200
    else:
        return Response("You do not have access rights", status=401, mimetype='application/json')


@module.route('/testData', methods=["GET"])
@jwt_required
def get_test_data():
    """
    Method for accessing test questions and answer possibilities (for single and multiple choice questions)
    :return: JSON with test
    """
    test = Tests.query.filter_by(name=request.args.get('test_name')).first()
    with open("app/tests/" + test.filename, "r") as file:
        data = file.read()
    return Response(data, status=200, mimetype='application/json')


@module.route('/testResults', methods=["POST"])
@jwt_required
def upload_test_results():
    """
    Method for uploading test answers for the server and getting grade. Method checks every answer and returns grade for the test.
    :return: grade for the test
    """
    user_login, user_role = get_token_info(request)

    if user_login == request.get_json().get('login'):
        test = Tests.query.filter_by(name=request.get_json().get('testName')).first()
        if not test:
            return Response("There is no test for given parameters", status=401, mimetype='application/json')
        if not is_test_available(user_login, test.name):
            return Response("Test already attempted or not available", status=401, mimetype='application/json')
        with open("app/tests/" + test.filename[:-4] + "Answers.txt", "r") as file:
            right_answers = file.read().splitlines()
        user_answers = request.get_json().get('answers')
        score = 0
        for i, answer in enumerate(user_answers):
            if str(answer) == right_answers[i]:
                score += 1
        result = int(100 * score / len(user_answers))
        handle_test_attempt(user_login, test.name, result)
        return Response(str(result), status=200, mimetype='application/json')
    else:
        return Response("You do not have access rights", status=401, mimetype='application/json')


def is_test_available(login, test_name):
    test_states = TestsStates.query.filter_by(candidate=login).all()
    for test_state in test_states:
        if test_state.test == test_name and test_state.status == "not attempted":
            return True
    return False


def handle_test_attempt(login, test_name, result):
    """
    Methods checks whether user's status need to be changed after test and sends email to his/her mail
    :param login: login of user
    :param test_name: name of test needs to be checked
    :param result: grade for the test
    """
    test_states = TestsStates.query.filter_by(candidate=login).all()
    successful_results = 0
    attempted_tests = 0
    for testState in test_states:
        if testState.test == test_name:
            testState.status = "graded"
            testState.result = result
        if float(testState.result) > 80:
            successful_results += 1
        if testState.status == "graded":
            attempted_tests += 1
    if attempted_tests == len(test_states):
        candidate = Candidate.query.get(request.get_json().get('login'))
        if successful_results == len(test_states):
            send_message(login, "Your status updated", "Your status updated to: " +
                         "PASSED TESTS. Now you will be assigned for interview")
            candidate.state = "PASSED_TESTS"
        else:
            candidate.state = "GRADED"
            candidate.grade = "T"
            send_message(login, "Your status updated", "Unfortunately you have not pass tests. Try next year")
    db.session.commit()


def send_async_email(msg):
    """
    Mehod sends email message asynchronously
    :param msg: message object
    """
    with app.app_context():
        mail.send(msg)


def send_message(to, msg, body):
    """
    Mehod redirects sending email message in other thread
    :param to: recepient
    :param msg: message theme
    :param body: message body
    """
    msg = Message(msg, sender='rozaliya_amirova@bk.ru', recipients=[to])
    msg.body = body
    thr = Thread(target=send_async_email, args=[msg])
    thr.start()


def get_token_info(request_data):
    """
    Method checks whether token in request is valid
    :param request_data: requests
    :return: login of user and role or error if token is invalid
    """
    headers = dict(request_data.headers)
    token = headers["Authorization"].split(' ')[1]
    tokens = Token.query.filter_by(token=token)
    if tokens.first():
        login = tokens.first().login
        role = User.query.get(login).role
        return login, role
    else:
        return "User not authorized", -1


@module.route('/grades', methods=["GET"])
@jwt_required
def get_test_grades():
    """
    Method returns grades for a given student. Login of student should be specified in body - JSON
    :return: 200 if OK; 401 if user do not have acces rights
    """
    user_login, user_role = get_token_info(request)

    if user_login == request.get_json().get('login') or user_role == 'manager' or user_role == 'staff_member':
        test_states = TestsStates.query.filter_by(candidate=request.get_json().get('login')).all()
        result = {}
        for test_state in test_states:
            result[test_state.test] = test_state.result
        return make_response(jsonify(result)), 200
    else:
        return Response("You do not have access rights", status=401, mimetype='application/json')
