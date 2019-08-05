from werkzeug.security import generate_password_hash, check_password_hash
#from flask_sqlalchemy import not_
from sqlalchemy.sql import exists
from flask_login import UserMixin
from datetime import datetime
from hashlib import md5
from time import time
from flask import current_app
import jwt
from app import db, login

#setting up the user table model
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    name = db.Column(db.String(30))
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    school_name = db.Column(db.String(255))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow) 
    #establishes a relationship with the Post table   
    questions = db.relationship('Question', backref='author', lazy='dynamic')
    papers = db.relationship('Paper', backref='author', lazy='dynamic')

    #Avatars, no registrations gives the identicon
    #Could easily change this later if gravatar isn't suitable
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    #methods for controlling password set and check with hashing
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    #tells python how to print objects of the class (debugging)
    def __repr__(self):
        user = 'User {}'.format(self.username) + ' id {}'.format(self.id)
        return user

    #Generates a token for password reset email
    def get_reset_password_token(self, expires_in=600):
            return jwt.encode(
                {'reset_password': self.id, 'exp': time() + expires_in},
                current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    #Verify the token to ensure security
    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

#handling user sessions
@login.user_loader #register with flask-login
def load_user(id):
    return User.query.get(int(id))


class Exam_Boards(db.Model):
    __tablename__ = 'exam_boards'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), index=True, unique=True)
    questions = db.relationship('Question', backref='examboard', lazy='dynamic')

    def __repr__(self):
        return '<Exam Board {}>'.format(self.name) 

class Question(db.Model):
    __tablename__ = 'question'
    id = db.Column(db.Integer, primary_key=True)
    #grabs the foreign key 'id' from the exam_boards table
    exam_board = db.Column(db.Integer, db.ForeignKey('exam_boards.id'))
    exam_year = db.Column(db.Integer)
    exam_session = db.Column(db.Integer)
    body = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    #grabs the foreign key 'id' from the user table
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    marks = db.Column(db.Integer)
    answer = db.Column(db.String(255))
    papers = db.relationship(
            'Paper', secondary='question_in', backref='has_question', lazy='dynamic')

    #def is_in_paper(self, paper):
     #   found = self.query.filter(Question.papers.any(id=self.id)).all()

      #  return found
        
class Paper(db.Model):
    __tablename__ = 'paper'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    total_marks = db.Column(db.Integer)
    date_created = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    #Paper has a virtual column called has_question
    
    def add(self, question):
        self.has_question.append(question)
        db.session.commit()

    def delete(self, question):
        self.has_question.remove(question)
        db.session.commit()


    #returns the questions in the paper
    def all_questions(self):
        questions = Question.query.filter(Question.papers.any(id=self.id)).all()
        
        return questions

    #return all the questions not used in a particular paper
    def not_used(self):
        assigned_questions = db.session.query(Question.id)\
                        .filter(Question.papers.any(id=self.id)).subquery()
        not_assigned = db.session.query(Question)\
                        .filter(Question.id.notin_(assigned_questions)).all()
        return not_assigned

Question_in = db.Table('question_in',
    db.Column('question_id', db.Integer, db.ForeignKey('question.id'), primary_key=True),
    db.Column('paper_id', db.Integer,db.ForeignKey('paper.id'), primary_key=True), 
)
