from app.database import db

class Manager(db.Model):
    __tablename__ = 'managers'

    login = db.Column(db.String(50), primary_key=True)
    password = db.Column(db.String(50))
    name = db.Column(db.String(20))
    surname = db.Column(db.String(20))
    second_name = db.Column(db.String(20))

    def __init__(self, login, password, name, surname, second_name):
        self.name = name
        self.login = login
        self.password = password
        self.surname = surname
        self.second_name = second_name


class Interview(db.Model):
    __tablename__ = 'interviews'
    id = db.Column(db.Integer, primary_key=True)
    student = db.Column(db.String(50))
    interviewer = db.Column(db.String(50))
    date = db.Column(db.Date)
    new = db.Column(db.Text)

    def __init__(self, student, interviewer, date, id):
        self.student = student
        self.id = id
        self.interviewer = interviewer
        self.date = date
        self.new = "new"


