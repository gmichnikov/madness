from collections import defaultdict
import math
from app.models import Team, Game, Round, Pick, User, Pool
from app import db

def get_win_probability(team_a, team_b, avg_o_rating):
    """
    Calculates the probability of team_a winning against team_b.
    Formula:
    X = (team_a_o * team_b_d) / avg_o
    Y = (team_b_o * team_a_d) / avg_o
    P(A wins) = X^10.5 / (X^10.5 + Y^10.5)
    """
    if not team_a.off_efficiency or not team_a.def_efficiency or \
       not team_b.off_efficiency or not team_b.def_efficiency or \
       not avg_o_rating:
        return 0.5
        
    try:
        x = (team_a.off_efficiency * team_b.def_efficiency) / avg_o_rating
        y = (team_b.off_efficiency * team_a.def_efficiency) / avg_o_rating
        
        x_p = math.pow(x, 10.5)
        y_p = math.pow(y, 10.5)
        
        return x_p / (x_p + y_p)
    except (OverflowError, ZeroDivisionError):
        # Fallback for extreme cases
        if team_a.off_efficiency > team_b.off_efficiency:
            return 1.0
        return 0.0

def calculate_expected_points(pool_id):
    """
    Calculates exact expected points for each user based on win probabilities.
    Uses DP to propagate probabilities through the bracket.
    Updates the cache on the User model and GameProbability model.
    """
    from app.models import GameProbability
    pool = Pool.query.get(pool_id)
    if not pool or not pool.avg_o_rating:
        return None

    # Check if cache is still valid
    if not pool.expected_standings_dirty:
        users = User.query.filter_by(pool_id=pool_id).filter(User.is_bracket_valid == True).order_by(User.expected_score.desc()).all()
        if users:
            return {
                'standings': [{
                    'user_id': u.id,
                    'full_name': u.full_name,
                    'current_score': u.currentscore,
                    'expected_score': u.expected_score
                } for u in users]
            }

    avg_o = pool.avg_o_rating
    teams = {t.id: t for t in Team.query.all()}
    all_games = Game.query.order_by(Game.round_id, Game.id).all()
    
    # Check if we have enough efficiency data
    teams_with_ratings = [t for t in teams.values() if t.off_efficiency and t.def_efficiency]
    if len(teams_with_ratings) < 2:
        return None

    # ... (DP calculation) ...
    game_team_probs = defaultdict(lambda: defaultdict(float))
    feeding_games = defaultdict(list)
    for g in all_games:
        if g.winner_goes_to_game_id:
            feeding_games[g.winner_goes_to_game_id].append(g.id)

    for g in all_games:
        if not feeding_games[g.id]:
            if g.team1_id:
                game_team_probs[g.id][g.team1_id] = 1.0
            if g.team2_id:
                game_team_probs[g.id][g.team2_id] = 1.0

    games_by_round = defaultdict(list)
    for g in all_games:
        games_by_round[g.round_id].append(g)
    
    round_ids = sorted(games_by_round.keys())
    team_win_game_prob = defaultdict(lambda: defaultdict(float))

    for rid in round_ids:
        for g in games_by_round[rid]:
            if g.winning_team_id:
                team_win_game_prob[g.id][g.winning_team_id] = 1.0
                if g.winner_goes_to_game_id:
                    game_team_probs[g.winner_goes_to_game_id][g.winning_team_id] = 1.0
                continue
            
            feeders = feeding_games[g.id]
            if not feeders:
                t1_id = g.team1_id
                t2_id = g.team2_id
                if t1_id and t2_id:
                    t1 = teams[t1_id]
                    t2 = teams[t2_id]
                    p1_wins = get_win_probability(t1, t2, avg_o)
                    team_win_game_prob[g.id][t1_id] = p1_wins
                    team_win_game_prob[g.id][t2_id] = 1.0 - p1_wins
                elif t1_id:
                    team_win_game_prob[g.id][t1_id] = 1.0
                elif t2_id:
                    team_win_game_prob[g.id][t2_id] = 1.0
            else:
                feeder1_probs = team_win_game_prob[feeders[0]]
                feeder2_probs = team_win_game_prob[feeders[1]] if len(feeders) > 1 else {}
                
                for t1_id, p1_reaches in feeder1_probs.items():
                    if p1_reaches == 0: continue
                    win_prob_given_reached = 0
                    if not feeder2_probs:
                        win_prob_given_reached = 1.0
                    else:
                        for t2_id, p2_reaches in feeder2_probs.items():
                            if p2_reaches == 0: continue
                            win_prob_given_reached += p2_reaches * get_win_probability(teams[t1_id], teams[t2_id], avg_o)
                    team_win_game_prob[g.id][t1_id] = p1_reaches * win_prob_given_reached
                
                for t2_id, p2_reaches in feeder2_probs.items():
                    if p2_reaches == 0: continue
                    win_prob_given_reached = 0
                    for t1_id, p1_reaches in feeder1_probs.items():
                        if p1_reaches == 0: continue
                        win_prob_given_reached += p1_reaches * get_win_probability(teams[t2_id], teams[t1_id], avg_o)
                    team_win_game_prob[g.id][t2_id] = p2_reaches * win_prob_given_reached

            if g.winner_goes_to_game_id:
                for t_id, p_win in team_win_game_prob[g.id].items():
                    game_team_probs[g.winner_goes_to_game_id][t_id] += p_win

    # 3. Store Game Probabilities
    GameProbability.query.delete()
    for g_id, probs in team_win_game_prob.items():
        for t_id, prob in probs.items():
            if prob > 0.0001: # Filter out near-zero for DB space
                db.session.add(GameProbability(game_id=g_id, team_id=t_id, probability=prob))

    # 4. Calculate Expected Scores for Users
    users = User.query.filter_by(pool_id=pool_id).filter(User.is_bracket_valid == True).all()
    user_expected_results = []

    all_picks = Pick.query.join(User).filter(User.pool_id == pool_id).filter(User.is_bracket_valid == True).all()
    user_picks_by_user = defaultdict(list)
    for p in all_picks:
        user_picks_by_user[p.user_id].append(p)

    for user in users:
        expected_score = float(user.currentscore)
        for pick in user_picks_by_user[user.id]:
            if pick.game.winning_team_id is None:
                prob = team_win_game_prob[pick.game_id][pick.team_id]
                expected_score += prob * pick.game.round.points
        
        user.expected_score = expected_score
        user_expected_results.append({
            'user_id': user.id,
            'full_name': user.full_name,
            'current_score': user.currentscore,
            'expected_score': expected_score
        })

    pool.expected_standings_dirty = False
    db.session.commit()

    user_expected_results.sort(key=lambda x: x['expected_score'], reverse=True)
    return {
        'standings': user_expected_results,
        'team_probs': team_win_game_prob
    }


def diagnose_zero_expected(pool_id):
    """
    Diagnostic: for valid-bracket users with expected_score 0, report why.
    Builds team_win_game_prob without modifying DB, then checks each pick.
    Returns a list of diagnostic dicts.
    """
    pool = Pool.query.get(pool_id)
    if not pool or not pool.avg_o_rating:
        return None

    avg_o = pool.avg_o_rating
    teams = {t.id: t for t in Team.query.all()}
    all_games = Game.query.order_by(Game.round_id, Game.id).all()
    game_ids = {g.id for g in all_games}

    teams_with_ratings = [t for t in teams.values() if t.off_efficiency and t.def_efficiency]
    if len(teams_with_ratings) < 2:
        return None

    # Build team_win_game_prob (same logic as calculate_expected_points, no DB write)
    game_team_probs = defaultdict(lambda: defaultdict(float))
    feeding_games = defaultdict(list)
    for g in all_games:
        if g.winner_goes_to_game_id:
            feeding_games[g.winner_goes_to_game_id].append(g.id)

    for g in all_games:
        if not feeding_games[g.id]:
            if g.team1_id:
                game_team_probs[g.id][g.team1_id] = 1.0
            if g.team2_id:
                game_team_probs[g.id][g.team2_id] = 1.0

    games_by_round = defaultdict(list)
    for g in all_games:
        games_by_round[g.round_id].append(g)

    round_ids = sorted(games_by_round.keys())
    team_win_game_prob = defaultdict(lambda: defaultdict(float))

    for rid in round_ids:
        for g in games_by_round[rid]:
            if g.winning_team_id:
                team_win_game_prob[g.id][g.winning_team_id] = 1.0
                if g.winner_goes_to_game_id:
                    game_team_probs[g.winner_goes_to_game_id][g.winning_team_id] = 1.0
                continue

            feeders = feeding_games[g.id]
            if not feeders:
                t1_id = g.team1_id
                t2_id = g.team2_id
                if t1_id and t2_id:
                    t1 = teams[t1_id]
                    t2 = teams[t2_id]
                    p1_wins = get_win_probability(t1, t2, avg_o)
                    team_win_game_prob[g.id][t1_id] = p1_wins
                    team_win_game_prob[g.id][t2_id] = 1.0 - p1_wins
                elif t1_id:
                    team_win_game_prob[g.id][t1_id] = 1.0
                elif t2_id:
                    team_win_game_prob[g.id][t2_id] = 1.0
            else:
                feeder1_probs = team_win_game_prob[feeders[0]]
                feeder2_probs = team_win_game_prob[feeders[1]] if len(feeders) > 1 else {}
                for t1_id, p1_reaches in feeder1_probs.items():
                    if p1_reaches == 0:
                        continue
                    win_prob_given_reached = 0
                    if not feeder2_probs:
                        win_prob_given_reached = 1.0
                    else:
                        for t2_id, p2_reaches in feeder2_probs.items():
                            if p2_reaches == 0:
                                continue
                            win_prob_given_reached += p2_reaches * get_win_probability(teams[t1_id], teams[t2_id], avg_o)
                    team_win_game_prob[g.id][t1_id] = p1_reaches * win_prob_given_reached
                for t2_id, p2_reaches in feeder2_probs.items():
                    if p2_reaches == 0:
                        continue
                    win_prob_given_reached = 0
                    for t1_id, p1_reaches in feeder1_probs.items():
                        if p1_reaches == 0:
                            continue
                        win_prob_given_reached += p1_reaches * get_win_probability(teams[t2_id], teams[t1_id], avg_o)
                    team_win_game_prob[g.id][t2_id] = p2_reaches * win_prob_given_reached

            if g.winner_goes_to_game_id:
                for t_id, p_win in team_win_game_prob[g.id].items():
                    game_team_probs[g.winner_goes_to_game_id][t_id] += p_win

    all_picks = Pick.query.join(User).filter(User.pool_id == pool_id).filter(User.is_bracket_valid == True).all()
    user_picks_by_user = defaultdict(list)
    for p in all_picks:
        user_picks_by_user[p.user_id].append(p)

    zero_users = User.query.filter_by(pool_id=pool_id).filter(User.is_bracket_valid == True, User.expected_score == 0).all()
    results = []
    for user in zero_users:
        picks = user_picks_by_user[user.id]
        unplayed = [p for p in picks if p.game.winning_team_id is None]
        sample_picks = []
        for pick in unplayed[:10]:
            prob = team_win_game_prob[pick.game_id][pick.team_id]
            team = teams.get(pick.team_id)
            team_name = team.get_display_name() if team else '?'
            sample_picks.append({
                'game_id': pick.game_id,
                'team_id': pick.team_id,
                'team_name': team_name,
                'prob': prob,
                'points': pick.game.round.points,
                'game_exists': pick.game_id in game_ids,
                'team_in_prob_map': pick.team_id in team_win_game_prob[pick.game_id],
            })
        results.append({
            'user_id': user.id,
            'full_name': user.full_name,
            'current_score': user.currentscore,
            'pick_count': len(picks),
            'unplayed_pick_count': len(unplayed),
            'sample_picks': sample_picks,
        })
    return results
