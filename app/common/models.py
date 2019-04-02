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


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    receiver = db.Column(db.String(50))
    body = db.Column(db.Text)
    status = db.Column(db.Integer)

    def __init__(self, receiver, body, status):
        self.receiver = receiver
        self.body = body
        self.status = status
