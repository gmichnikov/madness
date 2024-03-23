from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Email, Length, NumberRange, EqualTo
from app.models import Round, Team, Pick, User
import pytz
import os

EMAIL = 'Email (used for login, shown to admins)'
FULL_NAME = 'Full Name (shown to all users, please enter your real name, e.g. John Doe)'
TIEBREAKER_1 = 'Tiebreaker 1: Winner\'s Score in Final'
TIEBREAKER_2 = 'Tiebreaker 2: Loser\'s Score in Final'
POOL_ID = int(os.getenv('POOL_ID'))

class RegistrationForm(FlaskForm):
    email = StringField(EMAIL, validators=[DataRequired(), Email()])
    full_name = StringField(FULL_NAME, validators=[DataRequired()], render_kw={"placeholder": "Ryan Appleby"})
    password = PasswordField('Password', validators=[DataRequired(), Length(min=4)])
    time_zone = SelectField('Time Zone', choices=[(tz, tz) for tz in pytz.all_timezones], default='US/Eastern')
    tiebreaker_winner = IntegerField(TIEBREAKER_1, validators=[DataRequired()], default=0)
    tiebreaker_loser = IntegerField(TIEBREAKER_2, validators=[DataRequired()], default=0)
    submit = SubmitField('Register')

class EditProfileForm(FlaskForm):
    full_name = StringField(FULL_NAME)
    time_zone = SelectField('Time Zone', choices=[(tz, tz) for tz in pytz.all_timezones])
    tiebreaker_winner = IntegerField(TIEBREAKER_1, validators=[DataRequired()])
    tiebreaker_loser = IntegerField(TIEBREAKER_2, validators=[DataRequired()])
    submit = SubmitField('Update Profile')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class AdminPasswordResetForm(FlaskForm):
    email = SelectField('Select User', choices=[])  # Assuming this will be populated with user emails
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=4)])
    submit = SubmitField('Reset Password')

class AdminPasswordResetCodeForm(FlaskForm):
    email = SelectField('Select User', choices=[])
    submit = SubmitField('Generate Code')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    reset_code = StringField('Reset Code', validators=[DataRequired()])
    submit = SubmitField('Verify Code')

class ResetPasswordForm(FlaskForm):
    reset_code = StringField('Reset Code', validators=[DataRequired()])
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=4)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

class SuperAdminDeleteUserForm(FlaskForm):
    email = SelectField('Select User', choices=[])
    submit = SubmitField('Delete User')

class ManageRegionsForm(FlaskForm):
    region_1 = StringField('Region 1', default="Region 1")
    region_2 = StringField('Region 2', default="Region 2")
    region_3 = StringField('Region 3', default="Region 3")
    region_4 = StringField('Region 4', default="Region 4")
    submit = SubmitField('Update Regions')

class ManageTeamsForm(FlaskForm):
    team_1 = StringField('Team 1: Region 1, Seed 1')
    team_2 = StringField('Team 2: Region 1, Seed 2')
    team_3 = StringField('Team 3: Region 1, Seed 3')
    team_4 = StringField('Team 4: Region 1, Seed 4')
    team_5 = StringField('Team 5: Region 1, Seed 5')
    team_6 = StringField('Team 6: Region 1, Seed 6')
    team_7 = StringField('Team 7: Region 1, Seed 7')
    team_8 = StringField('Team 8: Region 1, Seed 8')
    team_9 = StringField('Team 9: Region 1, Seed 9')
    team_10 = StringField('Team 10: Region 1, Seed 10')
    team_11 = StringField('Team 11: Region 1, Seed 11')
    team_12 = StringField('Team 12: Region 1, Seed 12')
    team_13 = StringField('Team 13: Region 1, Seed 13')
    team_14 = StringField('Team 14: Region 1, Seed 14')
    team_15 = StringField('Team 15: Region 1, Seed 15')
    team_16 = StringField('Team 16: Region 1, Seed 16')
    team_17 = StringField('Team 17: Region 2, Seed 1')
    team_18 = StringField('Team 18: Region 2, Seed 2')
    team_19 = StringField('Team 19: Region 2, Seed 3')
    team_20 = StringField('Team 20: Region 2, Seed 4')
    team_21 = StringField('Team 21: Region 2, Seed 5')
    team_22 = StringField('Team 22: Region 2, Seed 6')
    team_23 = StringField('Team 23: Region 2, Seed 7')
    team_24 = StringField('Team 24: Region 2, Seed 8')
    team_25 = StringField('Team 25: Region 2, Seed 9')
    team_26 = StringField('Team 26: Region 2, Seed 10')
    team_27 = StringField('Team 27: Region 2, Seed 11')
    team_28 = StringField('Team 28: Region 2, Seed 12')
    team_29 = StringField('Team 29: Region 2, Seed 13')
    team_30 = StringField('Team 30: Region 2, Seed 14')
    team_31 = StringField('Team 31: Region 2, Seed 15')
    team_32 = StringField('Team 32: Region 2, Seed 16')
    team_33 = StringField('Team 33: Region 3, Seed 1')
    team_34 = StringField('Team 34: Region 3, Seed 2')
    team_35 = StringField('Team 35: Region 3, Seed 3')
    team_36 = StringField('Team 36: Region 3, Seed 4')
    team_37 = StringField('Team 37: Region 3, Seed 5')
    team_38 = StringField('Team 38: Region 3, Seed 6')
    team_39 = StringField('Team 39: Region 3, Seed 7')
    team_40 = StringField('Team 40: Region 3, Seed 8')
    team_41 = StringField('Team 41: Region 3, Seed 9')
    team_42 = StringField('Team 42: Region 3, Seed 10')
    team_43 = StringField('Team 43: Region 3, Seed 11')
    team_44 = StringField('Team 44: Region 3, Seed 12')
    team_45 = StringField('Team 45: Region 3, Seed 13')
    team_46 = StringField('Team 46: Region 3, Seed 14')
    team_47 = StringField('Team 47: Region 3, Seed 15')
    team_48 = StringField('Team 48: Region 3, Seed 16')
    team_49 = StringField('Team 49: Region 4, Seed 1')
    team_50 = StringField('Team 50: Region 4, Seed 2')
    team_51 = StringField('Team 51: Region 4, Seed 3')
    team_52 = StringField('Team 52: Region 4, Seed 4')
    team_53 = StringField('Team 53: Region 4, Seed 5')
    team_54 = StringField('Team 54: Region 4, Seed 6')
    team_55 = StringField('Team 55: Region 4, Seed 7')
    team_56 = StringField('Team 56: Region 4, Seed 8')
    team_57 = StringField('Team 57: Region 4, Seed 9')
    team_58 = StringField('Team 58: Region 4, Seed 10')
    team_59 = StringField('Team 59: Region 4, Seed 11')
    team_60 = StringField('Team 60: Region 4, Seed 12')
    team_61 = StringField('Team 61: Region 4, Seed 13')
    team_62 = StringField('Team 62: Region 4, Seed 14')
    team_63 = StringField('Team 63: Region 4, Seed 15')
    team_64 = StringField('Team 64: Region 4, Seed 16')
    submit = SubmitField('Update Teams')

class ManageRoundsForm(FlaskForm):
    round_1_points = IntegerField('1st Round Points', validators=[DataRequired(), NumberRange(min=0)])
    round_2_points = IntegerField('2nd Round Points', validators=[DataRequired(), NumberRange(min=0)])
    round_3_points = IntegerField('Sweet 16 Points', validators=[DataRequired(), NumberRange(min=0)])
    round_4_points = IntegerField('Elite 8 Points', validators=[DataRequired(), NumberRange(min=0)])
    round_5_points = IntegerField('Final 4 Points', validators=[DataRequired(), NumberRange(min=0)])
    round_6_points = IntegerField('Championship Points', validators=[DataRequired(), NumberRange(min=0)])

    submit = SubmitField('Update Points')

class AdminStatusForm(FlaskForm):
    user_email = SelectField('User', coerce=int)
    is_admin = BooleanField('Is Admin')
    submit = SubmitField('Update Admin Status')

class SortStandingsForm(FlaskForm):
    def __init__(self, *args, **kwargs):
        super(SortStandingsForm, self).__init__(*args, **kwargs)
        self.sort_field.choices = [
            ('full_name', 'Name'),
            ('currentscore', 'Total Score'),
            ('maxpossiblescore', 'Max Possible Score'),
            ('champion_team_name', 'Champion')
        ] + [(f'r{round.id}score', f'{round.name}') for round in Round.query.order_by(Round.id).all()]

        champion_teams = set(pick.team.name for pick in Pick.query.filter_by(game_id=63).join(Team, Pick.team_id == Team.id).join(User, Pick.user_id == User.id).filter(User.pool_id == POOL_ID))
        self.champion_filter.choices = [('Any', 'Any')] + [(team, team) for team in sorted(champion_teams)]

    sort_field = SelectField('Sort by')
    sort_order = SelectField('Order', choices=[('asc', 'Ascending'), ('desc', 'Descending')], default='asc')
    champion_filter = SelectField('Filter by Champion')
    name_filter = StringField('Filter by Name')
    submit = SubmitField('Sort and/or Filter')

class UserSelectionForm(FlaskForm):
    user = SelectField('View picks for: ', coerce=int)
    submit = SubmitField('View Picks')

class AnalyticsForm(FlaskForm):
    granularity = SelectField('Time Granularity', choices=[
        ('1', '1 minute'), 
        ('5', '5 minutes'), 
        ('10', '10 minutes'), 
        ('30', '30 minutes'), 
        ('60', '1 hour'), 
        ('1440', '1 day')], validators=[DataRequired()])
    category = SelectField('Category', choices=[], validators=[DataRequired()])
    submit = SubmitField('Submit')