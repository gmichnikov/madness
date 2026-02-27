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
    """Minimal form for CSRF. Team dropdowns are rendered in template loop."""
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

        champion_teams = set(pick.team.get_display_name() for pick in Pick.query.filter_by(game_id=63).join(Team, Pick.team_id == Team.id).join(User, Pick.user_id == User.id).filter(User.pool_id == POOL_ID))
        self.champion_filter.choices = [('Any', 'Any')] + [(team, team) for team in sorted(champion_teams)]

    sort_field = SelectField('Sort by')
    sort_order = SelectField('Order', choices=[('asc', 'Ascending'), ('desc', 'Descending')], default='asc')
    champion_filter = SelectField('Filter by Champion')
    name_filter = StringField('Filter by Name (press enter)')
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