from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    r1score = db.Column(db.Integer, default=0, nullable=False)
    r2score = db.Column(db.Integer, default=0, nullable=False)
    r3score = db.Column(db.Integer, default=0, nullable=False)
    r4score = db.Column(db.Integer, default=0, nullable=False)
    r5score = db.Column(db.Integer, default=0, nullable=False)
    r6score = db.Column(db.Integer, default=0, nullable=False)
    currentscore = db.Column(db.Integer, default=0, nullable=False)
    maxpossiblescore = db.Column(db.Integer, default=0, nullable=False)
    tiebreaker_winner = db.Column(db.Integer, default=0, nullable=False)
    tiebreaker_loser = db.Column(db.Integer, default=0, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Region(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, default="Region")

    def __repr__(self):
        return f'<Region {self.name}>'

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seed = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    region_id = db.Column(db.Integer, db.ForeignKey('region.id'), nullable=False)

    region = db.relationship('Region', backref=db.backref('teams', lazy=True))

    def __repr__(self):
        return f'<Team {self.name}>'
