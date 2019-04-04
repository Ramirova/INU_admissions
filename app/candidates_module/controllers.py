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
import app
import os
from werkzeug.utils import secure_filename

import flask_jwt_extended
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    jwt_refresh_token_required,
    get_jwt_identity,
    get_raw_jwt
)

from app.common.models import User
from app.managers_module.models import Interview
from .models import Candidate, Tests, TestsStates, db
from sqlalchemy.exc import SQLAlchemyError

module = Blueprint('candidates', __name__, url_prefix='/api/candidates')

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])


# @module.route('/change_profile', methods=["POST"])
# @jwt_required
# def change_profile_info():
#     candidate = Candidate.query.get(request.get_json().get('login'))
#     candidate.name =
#     candidate.surname =
#     candidate.
#     “name”: string,
#     “surname”: string,
#     “photo”: url?,
#     “role”: string ????
#     “status”: string -> optional,
#     “progress”: int(0.
#     .100).
#     return None


@module.route('/upload', methods=['POST'])
@jwt_required
def upload_file():
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


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@module.route('/register', methods=['POST'])
def register():
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
        for test in tests:
            new_test_progress = TestsStates(login, test.name)
            db.session.add(new_test_progress)

        db.session.commit()
        return Response("Success", status=200, mimetype='application/json')
    return Response("User with given login already exists", status=401, mimetype='application/json')


@module.route('/profileDetails', methods=['POST'])
@jwt_required
def profile_details():
    contact_number = request.get_json().get('telephone')
    program = request.get_json().get('program')
    nationality = request.get_json().get('country')
    skype = request.get_json().get('skype')

    candidate = Candidate.query.get(request.get_json().get('login'))
    if candidate:
        candidate.nationality = nationality
        candidate.skype = skype
        candidate.program = program
        candidate.phone_number = contact_number
        db.session.commit()
        return Response("Success", status=200, mimetype='application/json')
    return Response("User with given login does not exist", status=401, mimetype='application/json')


@module.route('/profile', methods=["GET"])
@jwt_required
def profile_info():
    candidate = Candidate.query.get(request.args.get('login'))
    response = {
        'telephone': candidate.phone_number,
        'email': candidate.login,
        'program': candidate.program,
        'country': candidate.nationality,
        'skype': candidate.skype,
    }
    return make_response(jsonify(response)), 200


@module.route('/interviews', methods=["GET"])
@jwt_required
def get_interviews():
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


@module.route('/testInfo', methods=["GET"])
@jwt_required
def get_tests():
    tests = TestsStates.query.filter_by(candidate=request.args.get('login')).all()
    response_data = []
    for test in tests:
        response_data.append({
            'test_name': test.test,
            'status': test.status,
            'result': test.result
        })
    return make_response(jsonify(response_data)), 200

@module.route('/testData', methods=["GET"])
@jwt_required
def get_test_data():
    test = Tests.query.filter_by(name=request.args.get('test_name')).first()
    with open("app/tests/" + test.filename, "r") as file:
        data = file.read()
    return Response(data, status=200, mimetype='application/json')