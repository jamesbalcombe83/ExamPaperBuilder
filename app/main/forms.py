from flask import request
from flask_wtf import FlaskForm
from wtforms import Field, StringField, PasswordField, BooleanField, SubmitField, \
    SelectField, IntegerField, TextAreaField
from wtforms.fields.html5 import DateField
from wtforms.validators import ValidationError, InputRequired, Email, EqualTo, Length, NumberRange
from wtforms.widgets import TextInput
from app.models import User

class MyInputRequired(InputRequired):
    field_flags = ()

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[MyInputRequired()])
    name = StringField('Name', validators=[MyInputRequired()])
    email = StringField('Email', validators=[MyInputRequired(), Email()])
    school_name = StringField('School_name', validators=[MyInputRequired(), Length(min=1, max=150)])
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

class TagListField(Field):
    widget = TextInput()

    def _value(self):
        if self.data:
            return u', '.join(self.data)
        else:
            return u''

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = [x.strip() for x in valuelist[0].split(',')]
        else:
            self.data = []

class BetterTagListField(TagListField):
    def __init__(self, label='', validators=None, remove_duplicates=True, **kwargs):
        super(BetterTagListField, self).__init__(label, validators, **kwargs)
        self.remove_duplicates = remove_duplicates

    def process_formdata(self, valuelist):
        super(BetterTagListField, self).process_formdata(valuelist)
        if self.remove_duplicates:
            self.data = list(self._remove_duplicates(self.data))

    @classmethod
    def _remove_duplicates(cls, seq):
        """Remove duplicates in a case insensitive, but case preserving manner"""
        d = {}
        for item in seq:
            if item.lower() not in d:
                d[item.lower()] = True
                yield item

class QuestionForm(FlaskForm):
    exam_board = SelectField('Exam Board', choices=[],coerce=int, validators=[MyInputRequired()])
    exam_level = SelectField('Exam Level', choices=[], coerce=int, validators=[MyInputRequired()])
    exam_year = IntegerField('Year of original Examination')
    exam_session = SelectField('Session of original Examination', choices=[
        ('1','Jan'), ('2', 'Feb'), ('3', 'Mar'),('4', 'Apr'),('5', 'May'),('6', 'Jun'),
        ('7', 'Jul'),('8', 'Aug'),('9', 'Sept'),('10', 'Oct'),('11', 'Nov'),('12', 'Dec'),])
    body = TextAreaField('Question body', validators=[MyInputRequired()])
    answer_space = BooleanField('Generate space for question answer automatically?',default=False)
    answer = TextAreaField('Answer body', validators=[MyInputRequired()])
    marks = IntegerField('Enter the number of marks', validators=[MyInputRequired()])
    tags = TagListField('Provide tags to identify the question')

    #add category, tags, etc
    submit = SubmitField('Submit')

class ExamBoardForm(FlaskForm):
    name = StringField('Exam board name', validators=[MyInputRequired()])
    submit = SubmitField('Submit')

class ExamLevelForm(FlaskForm):
    name = StringField('Exam level', validators=[MyInputRequired()])
    submit = SubmitField('Submit')

class CreatePaperForm(FlaskForm):
    name = StringField('Paper name', validators=[MyInputRequired()])
    exam_level = SelectField('Exam level', choices=[],coerce=int, validators=[MyInputRequired()])  
    subject = StringField('Subject', validators=[MyInputRequired()])
    duration = IntegerField('Duration of Exam in minutes', validators=[MyInputRequired(), NumberRange(min=1, message="Must be greater than 0")])
    date = DateField('Date of Exam', format='%Y-%m-%d')
    positions = StringField('Positions')
    rules = TextAreaField('Rules of Exam')
    submit = SubmitField('Create paper')
