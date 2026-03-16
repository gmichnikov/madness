from app import app, db
from app.models import User, Game
from app.routes import set_is_bracket_valid, recalculate_standings

def fix_all_user_validity_and_standings():
    with app.app_context():
        games = Game.query.all()
        games_dict = {g.id: g for g in games}
        users = User.query.all()
        
        print(f"Updating {len(users)} users...")
        for user in users:
            old_valid = user.is_bracket_valid
            old_score = user.currentscore
            old_max = user.maxpossiblescore
            
            # Recalculate validity
            set_is_bracket_valid(games_dict=games_dict, user=user, commit=False)
            
            # Recalculate standings (which includes maxpossiblescore)
            recalculate_standings(user=user, commit=False)
            
            # Status messages
            valid_changed = old_valid != user.is_bracket_valid
            score_changed = old_score != user.currentscore or old_max != user.maxpossiblescore
            
            if valid_changed or score_changed:
                print(f"User {user.email}: Updated.")
                if valid_changed:
                    print(f"  Valid: {old_valid} -> {user.is_bracket_valid}")
                if score_changed:
                    print(f"  Score: {old_score}/{old_max} -> {user.currentscore}/{user.maxpossiblescore}")
            else:
                print(f"User {user.email}: No changes needed.")
        
        db.session.commit()
        print("Done.")

if __name__ == "__main__":
    fix_all_user_validity_and_standings()
