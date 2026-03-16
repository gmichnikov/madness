from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
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

@app.context_processor
def inject_globals():
    venmo_username = os.environ.get('VENMO_USERNAME')
    venmo_amount = os.environ.get('VENMO_AMOUNT', '10.00')
    venmo_note = os.environ.get('VENMO_NOTE', 'March Madness 2026')
    venmo_url = None
    if venmo_username:
        from urllib.parse import quote
        params = f"txn=pay&amount={quote(str(venmo_amount))}&note={quote(venmo_note)}"
        venmo_url = f"https://venmo.com/{venmo_username}?{params}"
    return dict(
        measurement_id=os.environ.get('MEASUREMENT_ID'),
        venmo_pay_url=venmo_url,
    )


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
        # 1: 'Team Name',
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


@click.command('refresh-espn-teams')
@with_appcontext
def refresh_espn_teams_command():
    """Fetch NCAA teams from ESPN API and upsert into EspnTeam table."""
    from app.espn import refresh_espn_teams
    count = refresh_espn_teams()
    click.echo(f'Refreshed {count} teams from ESPN.')

app.cli.add_command(refresh_espn_teams_command)


@click.command('add-manual-team')
@click.argument('short_name')
@click.option('--display-name', help='Full name e.g. "Tarleton State Texans"')
@click.option('--abbrev', help='Abbreviation e.g. TARL')
@with_appcontext
def add_manual_team_command(short_name, display_name, abbrev):
    """Add a team manually (e.g. first-year D1 not in ESPN API). Use for bracket display; run set-espn-id when you find real ID for scores."""
    from app.espn import add_manual_espn_team
    et = add_manual_espn_team(short_name, display_name=display_name, abbreviation=abbrev)
    click.echo(f'Added: {et.short_display_name} (espn_id={et.espn_id} placeholder). Run "flask set-espn-id {et.short_display_name} <real_id>" after you find the real ID from "flask list-scoreboard-teams".')

app.cli.add_command(add_manual_team_command)


@click.command('set-espn-id')
@click.argument('short_name_or_placeholder_id')
@click.argument('real_espn_id', type=int)
@with_appcontext
def set_espn_id_command(short_name_or_placeholder_id, real_espn_id):
    """Update a manual team's placeholder espn_id to the real ESPN ID (from list-scoreboard-teams) so score sync works."""
    from app.espn import set_espn_id
    et = set_espn_id(short_name_or_placeholder_id, real_espn_id)
    if et:
        click.echo(f'Updated {et.short_display_name} espn_id -> {real_espn_id}')
    else:
        click.echo('Team not found. Use short_display_name or placeholder espn_id (e.g. 900001).', err=True)

app.cli.add_command(set_espn_id_command)


@click.command('list-scoreboard-teams')
@with_appcontext
def list_scoreboard_teams_command():
    """List teams from the NCAA tournament scoreboard so you can find ESPN IDs for manual teams."""
    from app.espn import fetch_scoreboard_teams
    teams = fetch_scoreboard_teams()
    if not teams:
        click.echo('No teams in scoreboard (bracket may not be published yet).')
        return
    for t in teams:
        click.echo(f"  {t['espn_id']:>6}  {t['short_display_name']}")

app.cli.add_command(list_scoreboard_teams_command)

from app import routes
