from flask import render_template, redirect, url_for, flash, request
from app import app, db
from app.models import User, Region, Team, Round, LogEntry
from flask_login import login_user, logout_user, login_required, current_user, LoginManager
from app.forms import RegistrationForm, LoginForm, AdminPasswordResetForm, ManageRegionsForm, ManageTeamsForm, ManageRoundsForm, AdminStatusForm
from functools import wraps
import os
from dotenv import load_dotenv
load_dotenv()

ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('Admin access required.')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Initialize the LoginManager
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('index.html', logged_in=True, full_name=current_user.full_name, email=current_user.email)
    else:
        return render_template('index.html', logged_in=False)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            flash('Email already registered.')
            return redirect(url_for('register'))
        
        new_user = User(email=form.email.data, full_name=form.full_name.data)
        new_user.set_password(form.password.data)
        # Automatically make user with ADMIN_EMAIL an admin
        if form.email.data == ADMIN_EMAIL:
            new_user.is_admin = True
            new_user.is_super_admin = True

        db.session.add(new_user)
        db.session.commit()

        log_entry = LogEntry(category='Register', current_user_id=new_user.id, description=f"Name: {new_user.full_name}, Email: {new_user.email}")
        db.session.add(log_entry)
        db.session.commit()

        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/admin/reset_password', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_reset_password():
    if not current_user.is_admin:
        return redirect(url_for('index'))

    form = AdminPasswordResetForm()
    form.email.choices = [(user.email, user.email) for user in User.query.all()]

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            user.set_password(form.new_password.data)
            db.session.commit()
            flash('Password reset successfully.')

            log_entry = LogEntry(category='Reset Password', current_user_id=current_user.id, description=f"{current_user.full_name} reset password of {user.full_name}")
            db.session.add(log_entry)
            db.session.commit()

        else:
            flash('User not found.')

    return render_template('admin/reset_password.html', form=form)

@app.route('/admin/manage_regions', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_manage_regions():
    form = ManageRegionsForm()
    if form.validate_on_submit():
        # Assuming you have 4 regions and they are in the database
        # Update each region with the data from the form
        for i in range(1, 5):
            region = Region.query.get(i)
            if region:
                region_name = getattr(form, f'region_{i}').data
                region.name = region_name
        db.session.commit()
        flash('Regions updated successfully.')

        log_entry = LogEntry(category='Manage Regions', current_user_id=current_user.id, description=f"{current_user.full_name} edited regions")
        db.session.add(log_entry)
        db.session.commit()

        return redirect(url_for('admin_manage_regions'))

    # Pre-populate form fields with current region names
    for i in range(1, 5):
        region = Region.query.get(i)
        if region:
            getattr(form, f'region_{i}').data = region.name

    return render_template('admin/manage_regions.html', form=form)

@app.route('/admin/manage_teams', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_manage_teams():
    form = ManageTeamsForm()
    if form.validate_on_submit():
        for i in range(1, 65):
            team = Team.query.get(i)
            if team:
                team_field = getattr(form, f'team_{i}')
                team.name = team_field.data
        db.session.commit()
        flash('Teams updated successfully.')

        log_entry = LogEntry(category='Manage Teams', current_user_id=current_user.id, description=f"{current_user.full_name} edited teams")
        db.session.add(log_entry)
        db.session.commit()

        return redirect(url_for('admin_manage_teams'))

    # Pre-populate form fields with current team names
    for i in range(1, 65):
        team = Team.query.get(i)
        if team:
            team_field = getattr(form, f'team_{i}')
            team_field.data = team.name

    return render_template('admin/manage_teams.html', form=form)

@app.route('/admin/manage_rounds', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_manage_rounds():
    form = ManageRoundsForm()
    if form.validate_on_submit():
        for i in range(1, 7):
            round = Round.query.get(i)
            if round:
                round_points = getattr(form, f'round_{i}_points').data
                round.points = round_points
        db.session.commit()
        flash('Rounds updated successfully.')

        log_entry = LogEntry(category='Manage Rounds', current_user_id=current_user.id, description=f"{current_user.full_name} edited round points")
        db.session.add(log_entry)
        db.session.commit()

        return redirect(url_for('admin_manage_rounds'))

    # Pre-populate form fields with current region names
    for i in range(1, 7):
        round = Round.query.get(i)
        if round:
            getattr(form, f'round_{i}_points').data = round.points

    return render_template('admin/manage_rounds.html', form=form)

@app.route('/super_admin/manage_admins', methods=['GET', 'POST'])
@login_required
def super_admin_manage_admins():
    if not current_user.is_super_admin:
        return redirect(url_for('index'))

    form = AdminStatusForm()
    form.user_email.choices = [(user.id, user.email) for user in User.query.filter(User.is_super_admin == False)]

    current_admins = User.query.filter_by(is_admin=True).all()

    if request.method == 'POST':
        if form.validate_on_submit():
            user = User.query.get(form.user_email.data)
            if user:
                user.is_admin = form.is_admin.data
                db.session.commit()
                flash('Admin status updated successfully.')

                log_entry = LogEntry(category='Manage Admins', current_user_id=current_user.id, description=f"{current_user.full_name} edited admin status of {user.full_name} to {user.is_admin}")
                db.session.add(log_entry)
                db.session.commit()

                return redirect(url_for('super_admin_manage_admins'))

    return render_template('super_admin/manage_admins.html', form=form, current_admins=current_admins)

@app.route('/admin/view_logs')
@admin_required
@login_required
def admin_view_logs():
    log_entries = LogEntry.query.order_by(LogEntry.timestamp.desc()).all()
    return render_template('admin/view_logs.html', log_entries=log_entries)
