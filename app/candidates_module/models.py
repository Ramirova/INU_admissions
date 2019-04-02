from app.database import db, JsonModel

class Candidate(db.Model, JsonModel):
    __tablename__ = 'candidates'

    login = db.Column(db.String(50), primary_key=True)
    password = db.Column(db.String(50))
    name = db.Column(db.String(20))
    surname = db.Column(db.String(20))
    second_name = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    nationality = db.Column(db.String(20))
    grade = db.Column(db.String(2))
    skype = db.Column(db.String(50))
    state = db.Column(db.String(20))
    interview = db.Column(db.Integer)
    program = db.Column(db.String(20))
    phone_number = db.Column(db.String(20))

    def __init__(self, login, password, name, surname, second_name, date_of_birth, nationality, skype, phone_number,
                 program):
        self.name = name
        self.login = login
        self.password = password
        self.surname = surname
        self.second_name = second_name
        self.date_of_birth = date_of_birth
        self.grade = None
        self.nationality = nationality
        self.skype = skype
        self.state = 'REGISTERED'
        self.interview = None
        self.program = program
        self.phone_number = phone_number
