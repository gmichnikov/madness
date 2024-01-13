from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    full_name = StringField('Full Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class AdminPasswordResetForm(FlaskForm):
    email = SelectField('Select User', choices=[])  # Assuming this will be populated with user emails
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=4)])
    submit = SubmitField('Reset Password')

class ManageRegionsForm(FlaskForm):
    region_1 = StringField('Region 1', default="Region 1")
    region_2 = StringField('Region 2', default="Region 2")
    region_3 = StringField('Region 3', default="Region 3")
    region_4 = StringField('Region 4', default="Region 4")
    submit = SubmitField('Update Regions')
