from flask import render_template, redirect, url_for, flash, request
from app import app, db
from app.models import User, Region
from flask_login import login_user, logout_user, login_required, current_user, LoginManager
from app.forms import RegistrationForm, LoginForm, AdminPasswordResetForm, ManageRegionsForm
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

        db.session.add(new_user)
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
        return redirect(url_for('admin_manage_regions'))

    # Pre-populate form fields with current region names
    for i in range(1, 5):
        region = Region.query.get(i)
        if region:
            getattr(form, f'region_{i}').data = region.name

    return render_template('admin/manage_regions.html', form=form)