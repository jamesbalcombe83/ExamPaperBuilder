from werkzeug.security import generate_password_hash, check_password_hash
#from flask_sqlalchemy import not_
from sqlalchemy.sql import exists
from app import db, login
from flask_login import UserMixin
from datetime import datetime, timedelta
from hashlib import md5
from time import time
from flask import current_app, url_for
import os, base64, jwt
import json

#a class others can inherit to handle meta pagination
#contains the the user items (paper & questions), the _meta for pagination
#and _links
class PaginatedAPIMixin(object):
    @staticmethod
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        resources = query.paginate(page, per_page, False)
        data = {
            'items': [item.to_dict() for item in resources.items],
            '_meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': resources.pages,
                'total_items': resources.total
            },
            '_links': {
                'self': url_for(endpoint, page=page, per_page=per_page,
                                **kwargs),
                'next': url_for(endpoint, page=page + 1, per_page=per_page,
                                **kwargs) if resources.has_next else None,
                'prev': url_for(endpoint, page=page - 1, per_page=per_page,
                                **kwargs) if resources.has_prev else None
            }
        }
        return data

#setting up the user table model
class User(PaginatedAPIMixin, UserMixin, db.Model):
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
    deleted = db.Column(db.DateTime, default=None)
    #tokens for API interaction
    token = db.Column(db.String(32), index=True, unique=True)
    token_expiration = db.Column(db.DateTime)

    def get_token(self, expires_in=3600):
        now = datetime.utcnow()
        if self.token and self.token_expiration > now + timedelta(seconds=60):
            return self.token
        self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token

    def revoke_token(self):
        self.token_expiration = datetime.utcnow() - timedelta(seconds=1)

    @staticmethod
    def check_token(token):
        user = User.query.filter_by(token=token).first()
        if user is None or user.token_expiration < datetime.utcnow():
            return None
        return user

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

    #for API JSON dictionary of all user data
    def to_dict(self, include_email=False):
        data = {
            'id': self.id,
            'username': self.username,
            #native date time, z means UTC
            'last_seen': self.last_seen.isoformat() + 'Z',
            'name': self.name,
            'school_name': self.school_name,
            'paper_count': self.papers.count(),
            'question_count': self.questions.count(),
            'deleted': self.deleted,
            '_links': {
                'self': url_for('api.get_user', id=self.id),
                'papers': url_for('api.get_papers', id=self.id),
                'questions': url_for('api.get_questions', id=self.id),
                'avatar': self.avatar(128)
            }
        }
        if include_email:
            data['email'] = self.email
        return data

    #handling the opposite route - only things users can set
    def from_dict(self, data, new_user=False):
        for field in ['username', 'email', 'name', 'school', 'deleted']:
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])

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

class Exam_Levels(db.Model):
    __tablename__ = 'exam_levels'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), index=True, unique=True)
    question = db.relationship('Question', backref='examlevel', lazy='dynamic')
    papers = db.relationship('Paper', backref='examlevel', lazy='dynamic')
    
class Question(PaginatedAPIMixin, db.Model):
    __tablename__ = 'question'
    id = db.Column(db.Integer, primary_key=True)
    #grabs the foreign key 'id' from the exam_boards table
    exam_board = db.Column(db.Integer, db.ForeignKey('exam_boards.id'))
    exam_level = db.Column(db.Integer, db.ForeignKey('exam_levels.id'))
    exam_year = db.Column(db.Integer)
    exam_session = db.Column(db.Integer)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    #grabs the foreign key 'id' from the user table
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    marks = db.Column(db.Integer)
    answer = db.Column(db.Text)
    answer_space = db.Column(db.Boolean, server_default="false")
    papers = db.relationship(
        'Paper', secondary='question_in', backref='has_question', lazy='dynamic')
    tags = db.relationship(
        'Tag',secondary='question_tag', backref="is_tagged", lazy='dynamic')

    def delete(self):
        all_papers = self.papers.all()
        for paper in all_papers:
            positions = json.loads(paper.positions)
            positions.remove(self.id)
            paper.positions = json.dumps(positions)
            paper.total_marks -= self.marks
        db.session.delete(self)
    
    #return a list of tag names only
    def all_tags(self):
        tags = self.tags.all()
        tag_names = []
        for tag in tags:
            tag_names.append(tag.name)
        return tag_names

    #for API JSON dictionary of all question data
    def to_dict(self):
        data = {
            'id': self.id,
            'author': self.author.name,
            'created': self.timestamp.isoformat() + 'Z',
            'paper_count': self.papers.count(),
            'exam_board': self.exam_board,
            'exam_level': self.exam_level,
            'exam_year': self.exam_year,
            'exam_session': self.exam_session,
            'body': self.body,
            'answer_space': self.answer_space,
            'answer': self.answer,
            'marks': self.marks,
            '_links': {
                'self': url_for('api.get_questions', id=self.id),
                'papers': url_for('api.get_papers', id=self.id),
                'author': url_for('api.get_user', id=self.id),
            }
        }
        return data

#tags
class Tag(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String, unique=True, nullable=False)
    #has a virtual column called is_tagged

#linking tags to question
Question_tag = db.Table('question_tag',
    db.Column('question_id', db.Integer, db.ForeignKey('question.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
)

class Paper(PaginatedAPIMixin, db.Model):
    __tablename__ = 'paper'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), index=True)
    subject = db.Column(db.String)
    exam_level = db.Column(db.Integer, db.ForeignKey('exam_levels.id'))
    duration = db.Column(db.Integer)
    date = db.Column(db.DateTime)
    rules = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    total_marks = db.Column(db.Integer, default=0)
    date_created = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    positions = db.Column(db.String)
    #Paper has a virtual column called has_question

    def add(self, question):
        self.has_question.append(question)
        self.total_marks += question.marks
        positions = json.loads(self.positions)
        positions.append(question.id)
        self.positions = json.dumps(positions)
        db.session.commit()

    def delete(self, question):
        self.has_question.remove(question)
        self.total_marks -= question.marks
        positions = json.loads(self.positions)
        positions.remove(question.id)
        self.positions = json.dumps(positions)
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

    #for API JSON dictionary of all question data
    def to_dict(self):
        data = {
            'id': self.id,
            'name': self.name,
            'author': self.author.name,
            'total': self.total_marks,
            'created': self.date_created.isoformat() + 'Z',
            'exam_level': self.exam_level,
            '_links': {
                'self': url_for('api.get_papers', id=self.id),
                'papers': url_for('api.get_questions', id=self.id),
                'author': url_for('api.get_user', id=self.id),
            }
        }
        return data

Question_in = db.Table('question_in',
    db.Column('question_id', db.Integer, db.ForeignKey('question.id'), primary_key=True),
    db.Column('paper_id', db.Integer,db.ForeignKey('paper.id'), primary_key=True),
)
