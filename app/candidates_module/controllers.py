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
from .models import Candidate, db
from sqlalchemy.exc import SQLAlchemyError

module = Blueprint('candidates', __name__, url_prefix='/candidates')

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

# @module.route('/login', methods=["POST"])
# def auth():
#     candidate = Candidate.query.get(request.get_json().get('login'))
#     auth_token = create_access_token(identity=candidate.login)
#     if auth_token:
#         response = {
#             'token': auth_token,
#             'refresh_token': create_refresh_token(identity=candidate.login)
#         }
#         return make_response(jsonify(response)), 200
#     return Response("", status=401, mimetype='application/json')


# The jwt_refresh_token_required decorator insures a valid refresh
# token is present in the request before calling this endpoint. We
# can use the get_jwt_identity() function to get the identity of
# the refresh token, and use the create_access_token() function again
# to make a new access token for this identity.
# @module.route('/refresh', methods=['POST'])
# @jwt_refresh_token_required
# def refresh():
#     current_user = get_jwt_identity()
#     ret = {
#         'access_token': create_access_token(identity=current_user)
#     }
#     return jsonify(ret), 200


@module.route('/profile', methods=["GET"])
@jwt_required
def profile_info():
    candidate = Candidate.query.get(request.args.get('login'))
    response = {
        'name': candidate.name,
        'surname': candidate.surname,
        'second_name': candidate.second_name,
        'date_of_birth': candidate.date_of_birth,
        'nationality': candidate.nationality,
    }
    return make_response(jsonify(response)), 200


@module.route('/change_profile', methods=["POST"])
@jwt_required
def change_profile_info():
    candidate = Candidate.query.get(request.get_json().get('login'))

    return None


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
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], candidate.login, filename))
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
    candidate = Candidate.query.get(request.get_json().get('login'))
    if not candidate:
        new_candidate = Candidate(login, password, name, surname, second_name, date_of_birth, nationality, skype)
        new_user = User(login, password, 'candidate')
        db.session.add(new_candidate)
        db.session.add(new_user)
        db.session.commit()
        return Response("Success", status=200, mimetype='application/json')
    return Response("User with given login already exists", status=201, mimetype='application/json')
