from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, IntegerField, BooleanField,
                     RadioField)
from wtforms.validators import InputRequired, Length


class CourseForm(FlaskForm):
    title = StringField('Title', validators=[InputRequired(),
                                             Length(min=10, max=100)])
    description = TextAreaField('Course Description',
                                validators=[InputRequired(),
                                            Length(max=200)])
    price = IntegerField('Price', validators=[InputRequired()])
    level = RadioField('Level',
                       choices=['Beginner', 'Intermediate', 'Advanced'],
                       validators=[InputRequired()])
    available = BooleanField('Available', default='checked')

class RegistrationForm(FlaskForm):
    username = StringField('Username',validators=[InputRequired()])
    email    = StringField('Email',valiadators=[Email()])
    password = StringField('Password',valiadators=[InputRequired(),Regexp()])
    confirmP = StringField('Confirm Password',valiadators=[InputRequired()])