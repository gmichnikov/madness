from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask.cli import with_appcontext
import click
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

def init_db():
    """ Function to initialize database with default values. """
    from .models import Region, Team, Round, Game

    print("init starting")
    with app.app_context():
        if Region.query.count() == 0:
            print("init regions")
            for i in range(1, 5):
                db.session.add(Region(name=f"Region {i}"))
            db.session.commit()

        if Team.query.count() == 0:
            print("init teams")
            for region_id in range(1, 5):
                for seed in range(1, 17):
                    name = f"Region {region_id}: Seed {seed}"
                    team = Team(seed=seed, name=name, region_id=region_id)
                    db.session.add(team)
            db.session.commit()

        if Round.query.count() == 0:
            print("init rounds")
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

        if Game.query.count() == 0:
            print("init teams")
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

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

app.cli.add_command(init_db_command)

def update_team_names():
    from .models import Team
    team_updates = {
        1: 'Siena',
        2: 'Rutgers',
        3: 'Wagner',
        4: 'Marist',
        5: 'Wofford',
        6: 'Elon',
        7: 'Troy',
        8: 'Iona',
        9: 'Yale',
        10: 'Duke',
        11: 'Rider',
        12: 'Brown',
        13: 'Drake',
        14: 'Davidson',
        15: 'Lamar',
        16: 'Miami',
        17: 'Dartmouth',
        18: 'Boston',
        19: 'Lafayette',
        20: 'Merrimack',
        21: 'DePaul',
        22: 'Butler',
        23: 'Bryant',
        24: 'Towson',
        25: 'Mercer',
        26: 'Lehigh',
        27: 'Manhattan',
        28: 'Furman',
        29: 'Temple',
        30: 'Baylor',
        31: 'Purdue',
        32: 'Xavier',
        33: 'Drexel',
        34: 'Auburn',
        35: 'Howard',
        36: 'Seattle',
        37: 'Cornell',
        38: 'Harvard',
        39: 'Stetson',
        40: 'Bradley',
        41: 'Liberty',
        42: 'Providence',
        43: 'Niagara',
        44: 'Clemson',
        45: 'Utah',
        46: 'Radford',
        47: 'Samford',
        48: 'Gonzaga',
        49: 'Belmont',
        50: 'Hofstra',
        51: 'Fordham',
        52: 'Oakland',
        53: 'Colgate',
        54: 'Hampton',
        55: 'Syracuse',
        56: 'Canisius',
        57: 'La Salle',
        58: 'Ohio',
        59: 'Campbell',
        60: 'Marshall',
        61: 'Longwood',
        62: 'Maine',
        63: 'Miami',
        64: 'Winthrop'
    }

    for team_id, team_name in team_updates.items():
        team = Team.query.get(team_id)
        if team:
            team.name = team_name
            db.session.add(team)
    
    db.session.commit()

@click.command('update-team-names')
@with_appcontext
def update_team_names_command():
    update_team_names()
    click.echo('Updated team names.')

app.cli.add_command(update_team_names_command)
