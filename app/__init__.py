from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv
import os
import csv

load_dotenv()

app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

from app.utils import is_after_cutoff

@app.context_processor
def context_processor():
    return dict(is_after_cutoff=is_after_cutoff())

from .models import Region, Team, Round, Game
with app.app_context():
    if Region.query.count() == 0:
        for i in range(1, 5):
            db.session.add(Region(name=f"Region {i}"))
        db.session.commit()

with app.app_context():
    if Team.query.count() == 0:
        for region_id in range(1, 5):
            for seed in range(1, 17):
                name = f"Region {region_id}: Seed {seed}"
                team = Team(seed=seed, name=name, region_id=region_id)
                db.session.add(team)
        db.session.commit()

with app.app_context():
    if Round.query.count() == 0:
        round1 = Round(name="1st Round", points=1)
        db.session.add(round1)
        round2 = Round(name="2nd Round", points=2)
        db.session.add(round2)
        round3 = Round(name="Sweet 16", points=3)
        db.session.add(round3)
        round4 = Round(name="Elite 8", points=4)
        db.session.add(round4)
        round5 = Round(name="Final 4", points=6)
        db.session.add(round5)
        round6 = Round(name="Championship", points=12)
        db.session.add(round6)
        db.session.commit()

with app.app_context():
    if Round.query.count() == 0:
        current_dir = os.path.dirname(__file__)
        file_path = os.path.join(current_dir, 'static', 'games.csv')

        # First Phase: Insert games without winner_goes_to_game_id
        with open(file_path, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                game = Game(
                    round_id=int(row[1]),
                    team1_id=int(row[3]) if row[3] else None,
                    team2_id=int(row[4]) if row[4] else None,
                    winning_team_id=int(row[5]) if row[5] else None
                )
                db.session.add(game)
                db.session.commit()

        # Second Phase: Update games with winner_goes_to_game_id
        with open(file_path, 'r') as file:
            reader = csv.reader(file)
            for row, game in zip(reader, Game.query.order_by(Game.id)):
                if row[2]:
                    game.winner_goes_to_game_id = int(row[2])
            db.session.commit()
