import os
from flask import Flask
from .database import db
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity
)

def create_app():
    app = Flask(__name__)
    app.config.from_object(os.environ['APP_SETTINGS'])

    app.config['JWT_SECRET_KEY'] = 'INUadmissionssecretkey123456789'
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False
    app.config['UPLOAD_FOLDER'] = "/files"

    jwt = JWTManager(app)

    db.init_app(app)
    with app.test_request_context():
        db.create_all()

    import app.candidates_module.controllers as candidates_module
    import app.managers_module.controllers as managers_module
    import app.staff_module.controllers as staff_module
    import app.common.controllers as common_module

    app.register_blueprint(candidates_module.module)
    app.register_blueprint(managers_module.module)
    app.register_blueprint(staff_module.module)
    app.register_blueprint(common_module.module)

    return app