from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from app import db

class Pool(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Pool {self.name}>'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    time_zone = db.Column(db.String(50), nullable=False, default='UTC')
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_super_admin = db.Column(db.Boolean, default=False, nullable=False)
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
    is_bracket_valid = db.Column(db.Boolean, default=False, nullable=False)
    last_bracket_save = db.Column(db.DateTime, nullable=True)
    pool_id = db.Column(db.Integer, db.ForeignKey('pool.id'), nullable=True)
    reset_code = db.Column(db.String(120), nullable=True)
    reset_code_expiration = db.Column(db.DateTime, nullable=True)

    pool = db.relationship('Pool', backref='users')

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

class Round(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    points = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f'<Round {self.name}>'
    
class LogEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    category = db.Column(db.String(100), nullable=False)
    current_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    description = db.Column(db.Text, nullable=False)

    current_user = db.relationship('User')

    def __repr__(self):
        return f'<LogEntry {self.timestamp} - {self.category}>'
    
class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    round_id = db.Column(db.Integer, db.ForeignKey('round.id'), nullable=False)
    winner_goes_to_game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=True)
    team1_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)
    team2_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)
    winning_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)

    # Relationships
    round = db.relationship('Round', backref='games')
    winner_goes_to_game = db.relationship('Game', remote_side=[id], uselist=False)
    team1 = db.relationship('Team', foreign_keys=[team1_id])
    team2 = db.relationship('Team', foreign_keys=[team2_id])
    winning_team = db.relationship('Team', foreign_keys=[winning_team_id])

    def __repr__(self):
        return f'<Game {self.id} - Round {self.round_id}>'
    
class Pick(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)

    # Relationships
    user = db.relationship('User', backref='picks')
    game = db.relationship('Game', backref='picks')
    team = db.relationship('Team', backref='picks')

    def __repr__(self):
        return f'<Pick {self.id} - User {self.user_id}, Game {self.game_id}, Team {self.team_id}>'

class Thread(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    hidden = db.Column(db.Boolean, default=False)

    creator = db.relationship('User')
    posts = db.relationship('Post', backref='thread', lazy='dynamic')

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    thread_id = db.Column(db.Integer, db.ForeignKey('thread.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    hidden = db.Column(db.Boolean, default=False)

    author = db.relationship('User')

class PotentialWinner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    potential_winner_ids = db.Column(db.String, nullable=False)  # Storing team IDs as a string
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    game = db.relationship('Game', backref='potential_winners')