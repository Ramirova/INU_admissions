from app.database import db

class User(db.Model):
    __tablename__ = 'users'

    login = db.Column(db.String(50), primary_key=True)
    password = db.Column(db.String(50))
    role = db.Column(db.String(50))

    def __init__(self, login, password, role):
        self.role = role
        self.login = login
        self.password = password