from flask import render_template, redirect, url_for, flash, request
from app import app, db
from app.models import User, Region, Team, Round, LogEntry, Game, Pick, Thread, Post
from flask_login import login_user, logout_user, login_required, current_user, LoginManager
from app.forms import RegistrationForm, LoginForm, AdminPasswordResetForm, ManageRegionsForm, ManageTeamsForm, ManageRoundsForm, AdminStatusForm, EditProfileForm, SortStandingsForm, UserSelectionForm
from functools import wraps
import os
import csv
from sqlalchemy import text
import pytz
from collections import defaultdict
from app.utils import is_after_cutoff, get_current_time, get_cutoff_time
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
CASUAL_DATETIME_FORMAT = '%b %d, %Y, %-I:%M %p '

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
        return render_template('index.html', logged_in=True, user=current_user)
    else:
        return render_template('hero.html', logged_in=False)

@app.route('/hero')
def hero():
    return render_template('hero.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            flash('Email already registered.')
            return redirect(url_for('register'))
        
        new_user = User(
            email=form.email.data,
            full_name=form.full_name.data,
            time_zone=form.time_zone.data,
            tiebreaker_winner=form.tiebreaker_winner.data,
            tiebreaker_loser=form.tiebreaker_loser.data
        )
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

        recalculate_standings()
        return redirect(url_for('admin_manage_rounds'))

    # Pre-populate form fields with current round points
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

@app.route('/admin/view_logs', methods=['GET', 'POST'])
@admin_required
@login_required
def admin_view_logs():
    user_tz = pytz.timezone(current_user.time_zone)

    users = User.query.order_by(User.full_name).all()
    categories = db.session.query(LogEntry.category).distinct().order_by(LogEntry.category).all()

    selected_user = 'Any'
    selected_category = 'Any'

    if request.method == 'POST':
        selected_user = request.form.get('user_full_name', 'Any')
        selected_category = request.form.get('category', 'Any')

        log_entries = LogEntry.query
        if selected_user != 'Any':
            log_entries = log_entries.join(User).filter(User.full_name == selected_user)
        if selected_category != 'Any':
            log_entries = log_entries.filter(LogEntry.category == selected_category)
    else:
        log_entries = LogEntry.query

    log_entries = log_entries.order_by(LogEntry.timestamp.desc()).all()

    for log in log_entries:
        localized_timestamp = log.timestamp.replace(tzinfo=pytz.utc).astimezone(user_tz)
        tz_abbr = localized_timestamp.tzname()  # Gets the time zone abbreviation
        log.formatted_timestamp = localized_timestamp.strftime('%Y-%m-%d, %I:%M:%S %p ') + tz_abbr
        log.user_full_name = log.current_user.full_name if log.current_user else "Unknown User"
    return render_template('admin/view_logs.html', log_entries=log_entries, users=users, categories=categories, selected_user=selected_user, selected_category=selected_category)

@app.route('/user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def user_profile(user_id):
    if is_after_cutoff():
        return redirect(url_for('standings'))

    user = User.query.get_or_404(user_id)
    form = EditProfileForm()

    if user_id != current_user.id:
        return render_template('user_profile.html', user=user)

    if form.validate_on_submit():
        user.full_name = form.full_name.data
        user.time_zone = form.time_zone.data
        user.tiebreaker_winner = form.tiebreaker_winner.data
        user.tiebreaker_loser = form.tiebreaker_loser.data
        db.session.commit()
        flash('Profile updated successfully.')

        log_entry = LogEntry(category='Edit Profile', current_user_id=current_user.id, description=f"{current_user.email} set name to {user.full_name} and timezone to {user.time_zone}")
        db.session.add(log_entry)
        db.session.commit()

        return redirect(url_for('user_profile', user_id=user_id))

    elif request.method == 'GET':
        form.full_name.data = user.full_name
        form.time_zone.data = user.time_zone
        form.tiebreaker_winner.data = user.tiebreaker_winner
        form.tiebreaker_loser.data = user.tiebreaker_loser
    return render_template('edit_user_profile.html', form=form, user=user)

@app.route('/users')
@login_required
def users():
    users = User.query.order_by(User.full_name).all()
    return render_template('users.html', users=users)

@app.route('/admin/verify_users', methods=['GET', 'POST'])
@admin_required
@login_required
def admin_verify_users():
    users = User.query.order_by(User.full_name).all()

    if request.method == 'POST':
        for user in users:
            user.is_verified = request.form.get('verified_' + str(user.id)) == 'on'
        db.session.commit()
        flash('User verifications updated successfully.')

        log_entry = LogEntry(category='Verify Users', current_user_id=current_user.id, description=f"{current_user.email} verified some users")
        db.session.add(log_entry)
        db.session.commit()

        return redirect(url_for('admin_verify_users'))

    return render_template('admin/verify_users.html', users=users)

@app.route('/super_admin/reset_games', methods=['GET', 'POST'])
@login_required
def super_admin_reset_games():
    if not current_user.is_super_admin:
        return redirect(url_for('index'))

    if request.method == 'POST':
        reset_game_table()
        flash('Game table reset successfully.')

        log_entry = LogEntry(category='Reset Games', current_user_id=current_user.id, description=f"{current_user.email} reset the games table")
        db.session.add(log_entry)
        db.session.commit()

        return redirect(url_for('admin_view_logs'))

    return render_template('super_admin/reset_games.html')

def reset_game_table():
    current_dir = os.path.dirname(__file__)
    file_path = os.path.join(current_dir, 'static', 'games.csv')

    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            game_id = int(row[0])
            game = Game.query.get(game_id)
            if game:
                game.round_id = int(row[1])
                game.winner_goes_to_game_id = int(row[2]) if row[2] else None
                game.team1_id = int(row[3]) if row[3] else None
                game.team2_id = int(row[4]) if row[4] else None
                game.winning_team_id = int(row[5]) if row[5] else None
                db.session.commit()

@app.route('/make_picks', methods=['GET', 'POST'])
@login_required
def make_picks():
    if is_after_cutoff():
        return redirect(url_for('standings'))

    games = Game.query.order_by(Game.id).all()
    teams = Team.query.all()
    rounds = rounds_dict()
    regions = regions_dict()
    user_picks = {pick.game_id: pick.team_id for pick in current_user.picks}

    teams_dict = {team.id: team for team in teams}
    potential_picks_map = {game.id: get_potential_picks(game.id, return_current_pick=False) for game in games}

    is_bracket_valid = current_user.is_bracket_valid
    user_tz = pytz.timezone(current_user.time_zone)
    last_save_formatted = None
    if current_user.last_bracket_save:
        last_save_localized = current_user.last_bracket_save.replace(tzinfo=pytz.utc).astimezone(user_tz)
        last_save_formatted = last_save_localized.strftime('%Y-%m-%d, %I:%M:%S %p ') + last_save_localized.tzname()

    if request.method == 'POST':
        if request.form['action'] == 'save_picks':
            for game in games:
                selected_team_id = request.form.get(f'game{game.id}')
                pick = Pick.query.filter_by(user_id=current_user.id, game_id=game.id).first()
                if selected_team_id:
                    selected_team_id = int(selected_team_id)
                    add_or_update_pick(pick, selected_team_id, game.id)
                else:
                    later_round_pick_team_id = get_later_round_pick(game, request.form)
                    if later_round_pick_team_id and later_round_pick_team_id in potential_picks_map[game.id]:
                        add_or_update_pick(pick, later_round_pick_team_id, game.id)
                    else:
                        # Delete existing pick if it exists
                        Pick.query.filter_by(user_id=current_user.id, game_id=game.id).delete()

            db.session.commit()
            flash('Your picks have been saved.')
            set_is_bracket_valid()
            recalculate_standings()
            return redirect(url_for('make_picks'))
        elif request.form['action'] == 'clear_picks':
            Pick.query.filter_by(user_id=current_user.id).delete()
            db.session.commit()

            log_entry = LogEntry(category='Clear Picks', current_user_id=current_user.id, description=f"{current_user.email} cleared their picks")
            db.session.add(log_entry)
            db.session.commit()

            set_is_bracket_valid()
            recalculate_standings()
            return redirect(url_for('make_picks'))
        elif request.form['action'] == 'fill_in_better_seeds':
            auto_fill_bracket()
            set_is_bracket_valid()
            recalculate_standings()
            return redirect(url_for('make_picks'))

    return render_template('make_picks.html', games=games, teams=teams, rounds=rounds, regions=regions, user_picks=user_picks, teams_dict=teams_dict, potential_picks_map=potential_picks_map, is_bracket_valid=is_bracket_valid, last_save=last_save_formatted)

def add_or_update_pick(pick, team_id, game_id):
    if pick:
        pick.team_id = team_id
    else:
        pick = Pick(user_id=current_user.id, game_id=game_id, team_id=team_id)
        db.session.add(pick)

def get_potential_winners(game):
    if game.winning_team_id:
        return [game.winning_team_id]

    if game.round_id == 1:
        return [team_id for team_id in [game.team1_id, game.team2_id] if team_id]

    # Otherwise, find the two games that lead to this game
    previous_games = Game.query.filter_by(winner_goes_to_game_id=game.id).all()
    potential_winners = []

    # Recursively call this function on the previous games
    for prev_game in previous_games:
        potential_winners.extend(get_potential_winners(prev_game))

    return potential_winners

# When return_current_pick is False (the initial call for each game), we ignore the current pick, so that we populate the dropdowns based on previous rounds. This also means an invalid pick (team lost in earlier round) will not appear in the dropdown as an option at all, though it will still be in the DB until picks are saved again.
def get_potential_picks(game_id, return_current_pick):
    game = Game.query.get(game_id)

    if return_current_pick:
        pick = Pick.query.filter_by(user_id=current_user.id, game_id=game_id).first()
        if pick:
            return [pick.team_id]

    if game.round_id == 1:
        return [team_id for team_id in [game.team1_id, game.team2_id] if team_id]

    # Otherwise, find the two games that lead to this game
    previous_games = Game.query.filter_by(winner_goes_to_game_id=game_id).all()
    potential_picks = []

    # Recursively call this function on the previous games, with return_current_pick=True
    for prev_game in previous_games:
        potential_picks.extend(get_potential_picks(prev_game.id, return_current_pick=True))

    return potential_picks

def get_later_round_pick(game, form):
    if game and game.winner_goes_to_game_id:
        next_game_pick_id = form.get(f'game{game.winner_goes_to_game_id}')
        
        if next_game_pick_id:
            return int(next_game_pick_id)
        else:
            return get_later_round_pick(game.winner_goes_to_game, form)

    return None

def set_is_bracket_valid():
    is_bracket_valid = True
    games = Game.query.all()
    for game in games:
        if game.round_id == 1:
            continue

        user_pick = Pick.query.filter_by(user_id=current_user.id, game_id=game.id).first()
        if not user_pick:
            is_bracket_valid = False
            break

        previous_games = Game.query.filter_by(winner_goes_to_game_id=game.id).all()

        previous_picks = [Pick.query.filter_by(user_id=current_user.id, game_id=prev_game.id).first() for prev_game in previous_games]
        if not all(previous_picks) or user_pick.team_id not in [pick.team_id for pick in previous_picks]:
            is_bracket_valid = False

    current_user.is_bracket_valid = is_bracket_valid
    current_user.last_bracket_save = datetime.utcnow()
    db.session.commit()

    if is_bracket_valid:
        log_entry = LogEntry(category='Valid Bracket', current_user_id=current_user.id, description=f"{current_user.email} saved a valid bracket")
        db.session.add(log_entry)
        db.session.commit()

def auto_fill_bracket():
    games = Game.query.all()
    teams = Team.query.all()
    teams_dict = {team.id: team for team in teams}

    for game in games:
        current_pick = Pick.query.filter_by(user_id=current_user.id, game_id=game.id).first()
        if current_pick is None:
            potential_picks = get_potential_picks(game.id, return_current_pick=False)
            
            best_team = None
            best_seed = float('inf')
            for team_id in potential_picks:
                team = teams_dict[team_id]
                if team.seed < best_seed:
                    best_seed = team.seed
                    best_team = team

            if best_team:
                new_pick = Pick(user_id=current_user.id, game_id=game.id, team_id=best_team.id)
                db.session.add(new_pick)

    db.session.commit()

    log_entry = LogEntry(category='Fill Better Seeds', current_user_id=current_user.id, description=f"{current_user.email} filled in the better seeds")
    db.session.add(log_entry)
    db.session.commit()

@app.route('/admin/set_winners', methods=['GET', 'POST'])
@admin_required
@login_required
def admin_set_winners():
    games = Game.query.filter(Game.team1_id.isnot(None), 
                              Game.team2_id.isnot(None)).order_by(Game.id).all()

    games_by_round_and_region = defaultdict(lambda: defaultdict(list))
    for game in games:
        round_name = game.round.name
        region_name = game.team1.region.name  # Assuming team1 and team2 are always in the same region
        games_by_round_and_region[round_name][region_name].append(game)

    if request.method == 'POST':
        for game in games:
            selected_team_id = request.form.get(f"game_{game.id}")
            if selected_team_id:
                selected_team_id = int(selected_team_id)
            else:
                selected_team_id = None

            previous_winning_team_id = game.winning_team_id
            if previous_winning_team_id is None and selected_team_id is None:
                pass
            elif previous_winning_team_id == selected_team_id:
                pass
            elif selected_team_id is None:   # clearing a previously set winner
                game.winning_team_id = None
                next_game = Game.query.filter_by(id=game.winner_goes_to_game_id).first()
                if next_game:
                    if next_game.team1_id == previous_winning_team_id:
                        next_game.team1_id = None
                    elif next_game.team2_id == previous_winning_team_id:
                        next_game.team2_id = None
                log_entry = LogEntry(category='Remove Winner', current_user_id=current_user.id, description=f"{current_user.email} cleared winner of {game.team1.name} vs {game.team2.name}")
                db.session.add(log_entry)
            elif previous_winning_team_id is None:   # setting a winner
                game.winning_team_id = selected_team_id
                next_game = Game.query.filter_by(id=game.winner_goes_to_game_id).first()
                if next_game:
                    if next_game.team1_id is None:
                        next_game.team1_id = selected_team_id
                    elif next_game.team2_id is None:
                        next_game.team2_id = selected_team_id
                log_entry = LogEntry(category='Set Winner', current_user_id=current_user.id, description=f"{current_user.email} set winner of {game.team1.name} vs {game.team2.name}")
                db.session.add(log_entry)
            else:   # switching winner
                game.winning_team_id = selected_team_id
                next_game = Game.query.filter_by(id=game.winner_goes_to_game_id).first()
                if next_game:
                    if next_game.team1_id == previous_winning_team_id:
                        next_game.team1_id = selected_team_id
                    elif next_game.team2_id == previous_winning_team_id:
                        next_game.team2_id = selected_team_id

                log_entry = LogEntry(category='Change Winner', current_user_id=current_user.id, description=f"{current_user.email} changed winner of {game.team1.name} vs {game.team2.name}")
                db.session.add(log_entry)

        db.session.commit()
        flash('Game winners updated.', 'success')

        recalculate_standings()
        return redirect(url_for('admin_set_winners'))

    return render_template('admin/set_winners.html', games_by_round_and_region=games_by_round_and_region)

def recalculate_standings():
    users = User.query.all()
    for user in users:
        user.r1score = user.r2score = user.r3score = user.r4score = user.r5score = user.r6score = 0
        potential_additional_points = 0

        for pick in user.picks:
            round_points = pick.game.round.points
            if pick.game.winning_team_id is not None and pick.game.winning_team_id == pick.team_id:
                if pick.game.round_id == 1:
                    user.r1score += round_points
                elif pick.game.round_id == 2:
                    user.r2score += round_points
                elif pick.game.round_id == 3:
                    user.r3score += round_points
                elif pick.game.round_id == 4:
                    user.r4score += round_points
                elif pick.game.round_id == 5:
                    user.r5score += round_points
                elif pick.game.round_id == 6:
                    user.r6score += round_points
            if pick.game.winning_team_id is None:
                if pick.team_id in get_potential_winners(pick.game):
                    potential_additional_points += round_points

        total_score = user.r1score + user.r2score + user.r3score + user.r4score + user.r5score + user.r6score
        user.currentscore = total_score
        user.maxpossiblescore = total_score + potential_additional_points
        db.session.commit()

@app.route('/standings', methods=['GET', 'POST'])
@login_required
def standings():
    sort_form = SortStandingsForm(sort_field='currentscore', sort_order='desc', champion_filter = 'Any')

    if sort_form.validate_on_submit():
        sort_field = sort_form.sort_field.data
        sort_order = sort_form.sort_order.data
        champion_filter = sort_form.champion_filter.data
    else:
        sort_field = 'currentscore'
        sort_order = 'desc'
        champion_filter = 'Any'

    users = User.query.all()
    champion_picks = {pick.user_id: pick.team.name for pick in Pick.query.filter_by(game_id=63).join(Team, Pick.team_id == Team.id)}
    for user in users:
        user.champion_team_name = champion_picks.get(user.id, "?")

    if champion_filter != 'Any':
        users = [user for user in users if champion_picks.get(user.id, "?") == champion_filter]

    users.sort(key=lambda x: (getattr(x, sort_field) if sort_field != 'champion_team_name' else getattr(x, 'champion_team_name', "?")), reverse=(sort_order == 'desc'))

    if sort_field == 'champion_team_name':
        for user in users:
            user.rank = ""
    else:
        last_score = None
        last_rank = 0
        tie_count = 1

        for user in users:
            current_score = getattr(user, sort_field)

            if current_score == last_score:
                user.rank = last_rank  # Tie
                tie_count += 1
            else:
                last_rank += tie_count  # Increment rank by the number of tied users
                user.rank = last_rank
                tie_count = 1

            last_score = current_score

    return render_template('standings.html', users=users, sort_form=sort_form, rounds=rounds_dict())

def rounds_dict():
    return {round.id: round.name for round in Round.query.all()}

def regions_dict():
    return {region.id: region.name for region in Region.query.all()}

@app.route('/view_picks/<int:user_id>', methods=['GET', 'POST'])
@login_required
def view_picks(user_id):
    if not current_user.is_admin and not is_after_cutoff() and user_id != current_user.id:
        return redirect(url_for('standings'))

    user = User.query.get_or_404(user_id)
    games = Game.query.order_by(Game.id).all()
    form = UserSelectionForm()
    form.user.choices = [(u.id, u.full_name) for u in User.query.order_by(User.full_name).all()]

    if form.validate_on_submit():
        selected_user_id = form.user.data
        return redirect(url_for('view_picks', user_id=selected_user_id))

    # Set default selection only if the form has not been submitted
    form.user.default = user_id
    form.process()

    user_picks = {pick.game_id: pick.team for pick in Pick.query.filter_by(user_id=user_id).join(Team, Pick.team_id == Team.id)}
    lost_teams = get_teams_that_lost()

    return render_template('view_picks.html', form=form, games=games, user_picks=user_picks, user=user, rounds=rounds_dict(), regions=regions_dict(), teams = Team.query.all(), lost_teams=lost_teams)

@app.route('/admin/cutoff_status')
@admin_required
@login_required
def admin_cutoff_status():
    return render_template('admin/cutoff_status.html', cutoff_status=is_after_cutoff(), current_time = get_current_time(), cutoff_time=get_cutoff_time())

@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_users():
    valid_bracket_filter = 'Any'
    verified_filter = 'Any'
    users = User.query

    if request.method == 'POST':
        valid_bracket_filter = request.form.get('valid_bracket', 'Any')
        verified_filter = request.form.get('verified', 'Any')

        if valid_bracket_filter in ['Yes', 'No']:
            users = users.filter_by(is_bracket_valid=(valid_bracket_filter == 'Yes'))
        if verified_filter in ['Yes', 'No']:
            users = users.filter_by(is_verified=(verified_filter == 'Yes'))

    users = users.all()
    return render_template('admin/users.html', users=users, valid_bracket_filter=valid_bracket_filter, verified_filter=verified_filter)

def get_teams_that_lost():
    lost_teams = []
    games = Game.query.all()
    
    for game in games:
        if game.winning_team_id:
            if game.team1_id != game.winning_team_id:
                lost_teams.append(game.team1_id)
            elif game.team2_id != game.winning_team_id:
                lost_teams.append(game.team2_id)

    return lost_teams

@app.route('/message_board')
@login_required
def message_board():
    if current_user.is_admin:
        threads = Thread.query.order_by(Thread.created_at.desc()).all()
    else:
        threads = Thread.query.filter_by(hidden=False).order_by(Thread.created_at.desc()).all()

    user_tz = pytz.timezone(current_user.time_zone)
    for thread in threads:
        last_post = Post.query.filter_by(thread_id=thread.id).order_by(Post.created_at.desc()).first()
        last_updated_utc = last_post.created_at if last_post else thread.created_at
        localized_last_updated = last_updated_utc.replace(tzinfo=pytz.utc).astimezone(user_tz)
        thread.last_updated = localized_last_updated.strftime(CASUAL_DATETIME_FORMAT) + localized_last_updated.tzname()

    # Sort threads by last updated time in descending order
    threads.sort(key=lambda x: x.last_updated, reverse=True)

    return render_template('message_board.html', threads=threads)

@app.route('/create_thread', methods=['GET', 'POST'])
@login_required
def create_thread():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')

        if not title or not content:
            flash('Title and content are required.')
            return redirect(url_for('create_thread'))

        new_thread = Thread(title=title[:100], creator_id=current_user.id)
        db.session.add(new_thread)
        db.session.commit()

        new_post = Post(content=content[:1000], author_id=current_user.id, thread_id=new_thread.id)
        db.session.add(new_post)
        db.session.commit()

        flash('New thread created.')

        log_entry = LogEntry(category='Create Thread', current_user_id=current_user.id, description=f"{current_user.email} created thread \"{title}\"")
        db.session.add(log_entry)
        db.session.commit()

        return redirect(url_for('message_board'))

    return render_template('create_thread.html')

@app.route('/thread/<int:thread_id>', methods=['GET', 'POST'])
@login_required
def thread(thread_id):
    thread = Thread.query.get_or_404(thread_id)

    if current_user.is_admin:
        posts = Post.query.filter_by(thread_id=thread_id).order_by(Post.created_at.desc()).all()
    else:
        if thread.hidden:
            return redirect(url_for('message_board'))
        posts = Post.query.filter_by(thread_id=thread_id).filter_by(hidden=False).order_by(Post.created_at.desc()).all()

    user_tz = pytz.timezone(current_user.time_zone)
    for post in posts:
        localized_timestamp = post.created_at.replace(tzinfo=pytz.utc).astimezone(user_tz)
        post.formatted_timestamp = localized_timestamp.strftime(CASUAL_DATETIME_FORMAT)  + localized_timestamp.tzname()

    if request.method == 'POST':
        content = request.form.get('content')

        if not content:
            flash('Post content cannot be empty.')
        else:
            new_post = Post(content=content[:1000], author_id=current_user.id, thread_id=thread.id)
            db.session.add(new_post)
            db.session.commit()
            flash('Your post has been added.')
            return redirect(url_for('thread', thread_id=thread_id))

    return render_template('thread.html', thread=thread, posts=posts)

@app.route('/hide_thread/<int:thread_id>')
@admin_required
def hide_thread(thread_id):
    thread = Thread.query.get_or_404(thread_id)
    thread.hidden = True
    log_entry = LogEntry(category='Hide Thread', current_user_id=current_user.id, description=f"Hid thread \"{thread.title}\"")
    db.session.add(log_entry)
    db.session.commit()
    return redirect(url_for('message_board'))

@app.route('/unhide_thread/<int:thread_id>')
@admin_required
def unhide_thread(thread_id):
    thread = Thread.query.get_or_404(thread_id)
    thread.hidden = False
    log_entry = LogEntry(category='Unhide Thread', current_user_id=current_user.id, description=f"Unhid thread \"{thread.title}\"")
    db.session.add(log_entry)
    db.session.commit()
    return redirect(url_for('message_board'))

@app.route('/hide_post/<int:post_id>')
@admin_required
def hide_post(post_id):
    post = Post.query.get_or_404(post_id)
    post.hidden = True
    log_entry = LogEntry(category='Hide Post', current_user_id=current_user.id, description=f"Hid post on thread \"{post.thread.title}\"")
    db.session.add(log_entry)
    db.session.commit()
    return redirect(url_for('thread', thread_id=post.thread_id))

@app.route('/unhide_post/<int:post_id>')
@admin_required
def unhide_post(post_id):
    post = Post.query.get_or_404(post_id)
    post.hidden = False
    log_entry = LogEntry(category='Unhide Post', current_user_id=current_user.id, description=f"Unhid post on thread \"{post.thread.title}\"")
    db.session.add(log_entry)
    db.session.commit()
    return redirect(url_for('thread', thread_id=post.thread_id))
