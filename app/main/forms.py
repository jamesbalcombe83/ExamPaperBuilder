from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, IntegerField, TextAreaField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from app.models import User

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    school_name = StringField('School_name', validators=[DataRequired(), Length(min=1, max=150)])
    submit = SubmitField('Submit')

    #overloaded constructor for when the username didn't change
    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    #check if there is an existing username or not, if is, error
    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')

class QuestionForm(FlaskForm):
    exam_board = SelectField('Exam Board', choices=[],coerce=int, validators=[DataRequired()])
    exam_year = IntegerField('Year of original Examination')
    exam_session = StringField('Session of original Examination (e.g. month)')
    body = TextAreaField('Question', validators=[DataRequired(), Length(min=1, max=255)])
    answer = TextAreaField('Answer', validators=[DataRequired(), Length(min=1, max=255)])
    marks = IntegerField('Enter the number of marks', validators=[DataRequired()])

    #add category, tags, etc 
    submit = SubmitField('Submit')

class EditQuestionForm(FlaskForm):
    exam_board = SelectField('Exam Board', choices=[],coerce=int, validators=[DataRequired()])  
    exam_year = IntegerField('Year of original Examination')
    exam_session = StringField('Session of original Examination (e.g. month)')
    body = TextAreaField('Question', validators=[DataRequired(), Length(min=1, max=255)])
    answer = TextAreaField('Answer', validators=[DataRequired(), Length(min=1, max=255)])
    marks = IntegerField('Enter the number of marks', validators=[DataRequired()])

    submit = SubmitField('Submit')

class ExamBoardForm(FlaskForm):
    name = StringField('Exam board name', validators=[DataRequired()])
    submit = SubmitField('Submit')

class CreatePaperForm(FlaskForm):
    name = StringField('Paper name', validators=[DataRequired()])
    submit = SubmitField('Create paper')
