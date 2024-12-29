from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, IntegerField, BooleanField,
                     RadioField,EmailField,PasswordField)
from wtforms.validators import InputRequired, Length, Email, EqualTo ,Regexp


class CourseForm(FlaskForm):
    title = StringField('Title', validators=[InputRequired(),
                                             Length(min=10, max=100)]) #ความยาวของข้อความอย่างน้อยmin -> max
    description = TextAreaField('Course Description',
                                validators=[InputRequired(),
                                            Length(max=200)])
    price = IntegerField('Price', validators=[InputRequired()])
    level = RadioField('Level',
                       choices=['Beginner', 'Intermediate', 'Advanced'],
                       validators=[InputRequired()])
    available = BooleanField('Available', default='checked')

class RegistrationForm(FlaskForm):
    username = StringField('Username',validators=[InputRequired(),Length(min=2, max=20)])
    email = EmailField('Email',validators=[Email(message="Invalid Email")])
    password = PasswordField('Password',validators=[Regexp(r'(.*\d+.*)',message="Password must contain at least one number")])
    confirm_password = PasswordField('Confirm Password',validators=[EqualTo('password',message= "Passwords must match")])