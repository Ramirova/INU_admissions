from app.database import db

class Staff_member(db.Model):
    __tablename__ = 'staff'

    login = db.Column(db.String(50), primary_key=True)
    password = db.Column(db.String(50))
    name = db.Column(db.String(20))
    surname = db.Column(db.String(20))
    second_name = db.Column(db.String(20))
    position = db.Column(db.String(20))

    def __init__(self, login, password, name, surname, second_name, position):
        self.name = name
        self.login = login
        self.password = password
        self.surname = surname
        self.second_name = second_name
        self.position = position
