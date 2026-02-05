# March Madness Pool - 2026 Reboot Guide

## Overview

This is a Flask-based web application for hosting a March Madness basketball tournament pool. Users register, fill out their brackets, and compete for points as the tournament progresses. The admin manages teams, sets winners, and maintains the pool.

---

## System Architecture

### Key Components

1. **Flask Backend** (`app/routes.py`, `app/__init__.py`)
   - User authentication & registration
   - Bracket management
   - Admin controls for tournament progression
   - Message board/forum functionality

2. **Database Models** (`app/models.py`)
   - User (authentication, scores, tiebreakers)
   - Pool (for multi-pool support)
   - Region (4 regions in tournament)
   - Team (64 teams)
   - Round (6 rounds with point values)
   - Game (63 games total)
   - Pick (user selections for each game)
   - LogEntry (audit trail)
   - Thread/Post (message board)
   - PotentialWinner (cached data for standings calculation)

3. **Frontend Templates** (`app/templates/`)
   - Bootstrap-based responsive design
   - Bracket grid visualization
   - Admin management pages

4. **Deployment**
   - Configured for Heroku (`Procfile`, `runtime.txt`)
   - PostgreSQL database
   - Gunicorn web server

---

## 1. Cleanup Steps for 2026

### A. Code Cleanup [DONE]

#### **Remove/Update Outdated Features**

1. **GamePicksStats Model & Related Code** [DONE]
   - **Issue**: This appears to be a one-time statistics snapshot from 2024. The code also contains a hardcoded user count (167) from that year.
   - **Action**: 
     - [x] Remove the `GamePicksStats` model from `app/models.py`
     - [x] Remove the `populate_game_picks_stats()` function from `app/__init__.py`
     - [x] Remove the `/game_stats` route from `app/routes.py`
     - [x] Remove the `app/templates/game_stats.html` template
     - [x] Create a migration to drop the table: `flask db migrate -m "Remove GamePicksStats table"`

2. **Hardcoded Team Names** (`app/__init__.py`) [DONE]
   - **Issue**: The `update_team_names()` function has hardcoded 2024 team names
   - **Action**: 
     - [x] Keep the function structure for 2026 use
     - [x] Clear out the 2024 team names from the dictionary
     - You'll populate this with 2026 teams when Selection Sunday happens

3. **Cutoff Date** (`app/utils.py`) [DONE]
   - **Issue**: Hardcoded to March 21, 2024
   - **Action**: [x] Update to March 2026 date (Selection Sunday is usually mid-March)
   ```python
   def get_cutoff_time():
       naive_cutoff_time = datetime(2026, 3, 19, 12, 10)  # Updated
       cutoff_time = EASTERN.localize(naive_cutoff_time)
       return cutoff_time
   ```

4. **Analytics Date** (`app/routes.py`) [DONE]
   - **Issue**: `admin_analytics` has a hardcoded date `datetime(2024, 3, 17, 23, 0, 0)` for log filtering.
   - **Action**: [x] Update to 2026 Selection Sunday date.

5. **Update Python Version** (`runtime.txt`, `.python-version`) [DONE]
   - **Issue**: Python 3.9.18 is getting old
   - **Action**: [x] Update to Python 3.11 (matches gmich)
   ```
   3.11
   ```

6. **Update Dependencies** (`requirements.txt`) [DONE]
   - **Issue**: 2-year-old packages with potential security vulnerabilities
   - **Action**: 
    - [x] Update Flask, SQLAlchemy, and other dependencies to match gmich standards
    - [x] Test thoroughly after updating
     - [ ] Consider using `pip-audit` to check for vulnerabilities

### B. Database Cleanup [DONE - FRESH DB]

Your local database is currently empty and represents a fresh start for 2026. The original Heroku database no longer exists.

#### **Reset Tournament Data** [N/A - FRESH DB]

The following steps are traditionally used for season-to-season rollovers on an existing database. They are not required for your initial 2026 setup.

1. **Clear Old Tournament Results**
   - All `Game.winning_team_id` should be set to NULL
   - All `Game.team1_id` and `Game.team2_id` for games beyond Round 1 should be NULL
   - All `Pick` records should be deleted (or keep for historical reference in separate table)
   - All `PotentialWinner` records should be reset

2. **Reset User Data**
   - Set all user scores to 0 (r1score through r6score, currentscore, maxpossiblescore)
   - Set all `is_bracket_valid` to FALSE
   - Set all `last_bracket_save` to NULL

3. **Admin Utilities**
   - Consider implementing a `reset-tournament` CLI command in future seasons if needed to automate the above steps.

### C. Configuration Updates [DONE]

1. **Environment Variables** (`.env` file - not in repo) [DONE]
   - `DATABASE_URL`: PostgreSQL connection string
   - `SECRET_KEY`: Flask secret key
   - `ADMIN_EMAIL`: Email that gets auto-admin privileges
   - `POOL_ID`: Which pool to use (probably 1)
   - `MEASUREMENT_ID`: Google Analytics ID (optional)

2. **Pool Configuration** [DONE]
   - [x] Ensure your Pool record exists with correct name
   - [x] Update pool name to "March Madness 2026" or similar

---

## 2. Pre-Tournament Admin Setup

### Timeline: Between Selection Sunday and First Game

**Selection Sunday** (usually mid-March) → **First Four Games** (Tuesday/Wednesday) → **Round 1** (Thursday/Friday)

### Step-by-Step Process

#### **1. Update Regions** [TESTED]
- Navigate to: Admin → Edit Regions
- Update region names:
  - Region 1: [East/West/South/Midwest]
  - Region 2: [East/West/South/Midwest]
  - Region 3: [East/West/South/Midwest]
  - Region 4: [East/West/South/Midwest]

#### **2. Update Teams** [TESTED]
- Navigate to: Admin → Edit Teams
- Manually enter all 64 teams with their seeds
- **IMPORTANT**: Teams are pre-assigned to regions by ID:
  - Team IDs 1-16: Region 1
  - Team IDs 17-32: Region 2
  - Team IDs 33-48: Region 3
  - Team IDs 49-64: Region 4
- Match the actual bracket structure to these IDs
- **OR** use the `update_team_names()` function:
  ```python
  flask update-team-names
  ```
  (After you've updated the dictionary in `app/__init__.py`)

#### **3. Verify Round Points** [TESTED]
- Navigate to: Admin → Edit Round Points
- Default values:
  - Round 1: 1 point
  - Round 2: 2 points
  - Sweet 16: 3 points
  - Elite 8: 4 points
  - Final 4: 6 points
  - Championship: 12 points
- Adjust if you want different scoring

#### **4. Set Registration Cutoff** [TESTED]
- Update `app/utils.py` with the exact cutoff time
- This is when users can no longer edit brackets
- Typically set to tip-off of first game (Thursday ~noon ET)

#### **5. Test the Bracket** [TESTED]
- Create a test account
- Fill out a complete bracket
- Verify:
  - All games show correct matchups
  - Auto-fill feature works
  - Bracket validation works
  - Dropdown options are correct

#### **6. Open Registration** [TESTED]
- Share the registration link with participants
- Monitor registrations via: Admin → Users Status
- Verify users as they register: Admin → Verify Users

---

## 3. During Tournament Admin Tasks

### Daily/As Games Complete

#### **1. Set Game Winners** [TESTED]
- Navigate to: Admin → Set Game Winners
- Select winner for each completed game
- **IMPORTANT**: The system automatically:
  - Advances winners to next round games
  - Clears future round games if you change a winner
  - Logs all winner changes

#### **2. Update Standings** [TESTED]
- The system does NOT auto-update standings
- Navigate to: Super Admin → Update Potential Winners/Standings
- Click the link to trigger recalculation
- This updates:
  - All user scores
  - Max possible scores
  - Potential winners cache

#### **3. Monitor the Pool** [TESTED]
- Check: Admin → View Logs (for unusual activity)
- Check: Standings (to see current rankings)
- Check: Message Board (for user questions/complaints)

### Weekly Tasks

#### **1. Check for Issues**
- Admin → Users Status
  - Verify bracket validity
  - Check for scoring anomalies

#### **2. Engagement**
- Post updates on Message Board
- Share interesting statistics
- Highlight leader changes

---

## 4. Important Things to Keep in Mind

### A. Critical System Behaviors

1. **Bracket Access Control**
   - Once `is_after_cutoff()` returns True, users CANNOT edit brackets.
   - This logic is strictly enforced based on the system clock—ensure server time is accurate.
   - Test this thoroughly before tournament.

2. **Bracket Validation Logic**
   - A bracket is only valid if ALL games beyond Round 1 have picks.
   - Picks must match previous round winners (ensures a logical path through the bracket).
   - The "Fill In Better Seeds" button provides a convenient way for users to complete their bracket based on seeding.
   - Users can save invalid brackets for progress, but they will not be included in official scoring until valid.

3. **Scoring Logic** (`recalculate_standings()`)
   - Only runs when admin triggers it (not automatic!)
   - Scores correct picks that have been decided
   - Calculates max possible points based on remaining games
   - Uses cached `PotentialWinner` data for efficiency

4. **Winner Changes**
   - Changing a game winner cascades to future rounds
   - This can invalidate user brackets retroactively
   - All changes are logged
   - **BE CAREFUL** when correcting mistakes

### B. Database Considerations

1. **Pool Isolation**
   - The system supports multiple pools (`POOL_ID` in config)
   - All user queries filter by pool_id
   - Users can only see data from their pool
   - LogEntry shows all pools (potential issue if running multiple)

2. **Performance**
   - `PotentialWinner` table caches complex calculations
   - Must be updated when game winners change
   - The `get_potential_winners()` function is recursive and slow
   - Consider adding indexes if pool gets very large (100+ users)

3. **Data Integrity**
   - No foreign key cascades are set up
   - Deleting users requires manual cleanup (Super Admin → Delete User handles this)
   - The `games.csv` defines the bracket structure - don't modify it

### C. User Experience Issues

1. **Mobile Responsiveness**
   - Bracket grid can be hard to use on mobile
   - Consider warning users to use desktop for bracket entry
   - Viewing brackets on mobile is okay

2. **Autosave Feature**
   - Enabled by default (localStorage setting)
   - Saves on every dropdown change
   - Can be slow if many users are active simultaneously
   - Users can disable it

3. **Timezone Handling**
   - Users select their timezone on registration
   - All displayed times are converted to user's timezone
   - Cutoff time is in Eastern Time (hardcoded)

### D. Security Considerations

1. **Admin Access**
   - Email matching `ADMIN_EMAIL` env var gets auto-admin on registration
   - Super admin can promote users to admin
   - Admins can see all brackets, even before cutoff
   - Admins cannot be deleted (except by super admin)

2. **User Verification**
   - `is_verified` field exists but isn't enforced anywhere
   - Consider using it to prevent fake accounts
   - Currently it's just informational

3. **Password Reset**
   - Admin can generate reset codes (24-hour expiration)
   - Admin must manually share codes with users
   - No email system is implemented

### E. Current Roadmap & Enhancements

1. **Email System Integration**
   - Currently, user communication is handled manually.
   - Password resets are initiated by admins.
   - Automated notifications are a planned future enhancement.

2. **Real-Time Data**
   - Users currently refresh to see updated standings.
   - Future versions may include live polling or WebSocket updates.

3. **Expanded Pool Customization**
   - The current UI is optimized for a single primary pool.
   - Multi-pool management is supported by the database and can be expanded in the UI.

4. **Standings Automation**
   - Standings updates are currently triggered manually by administrators to ensure data integrity.
   - Integration with a scheduler (like Celery or Heroku Scheduler) is a recommended upgrade.

5. **First Four Tournament Handling**
   - The standard bracket model assumes a 64-team field.
   - Play-in games (First Four) can be handled via:
     - Option A: Focus on the main 64-team bracket.
     - Option B: Update Round 1 matchups after the First Four conclude.
     - Option C: Implement a dedicated "Round 0" (requires architectural update).

### F. Testing Checklist

Before going live:

- [x] Migration Test: Run `flask db upgrade` on a local copy of 2024 database to ensure path is clean
- [x] Database reset successfully
- [x] Regions updated with 2026 regions
- [x] All 64 teams entered correctly
- [x] Teams match their region assignments
- [x] Round points configured
- [x] Cutoff time set correctly
- [x] Test user can register
- [x] Test user can fill out complete bracket
- [x] Test user can save bracket
- [x] Bracket validation works
- [x] Auto-fill works correctly
- [x] Cutoff time prevents edits
- [x] Admin can set winners
- [x] Winners advance correctly
- [x] Standings update correctly
- [x] Message board works
- [x] Admin tools all accessible
- [ ] Mobile view acceptable
- [ ] Analytics working (if enabled)

---

## 5. Deployment Checklist

### Heroku Deployment (New App for 2026)

Since the original Heroku application has been retired, a new application must be created.

1. **Create New Heroku App**
   ```bash
   heroku create march-madness-2026
   ```

2. **Set Environment Variables**
   - [ ] Set `DATABASE_URL` (Done automatically by Postgres addon)
   - [ ] Set `SECRET_KEY`
   - [ ] Set `ADMIN_EMAIL`
   - [ ] Set `POOL_ID`
   ```bash
   heroku config:set SECRET_KEY='your-secret-key'
   heroku config:set ADMIN_EMAIL='your-email@example.com'
   heroku config:set POOL_ID=1
   heroku config:set MEASUREMENT_ID='GA-tracking-id'  # optional
   ```

3. **PostgreSQL Setup**
   ```bash
   heroku addons:create heroku-postgresql:mini
   # DATABASE_URL is set automatically
   ```

4. **Deploy**
   ```bash
   git push heroku main
   ```

5. **Run Migrations**
   ```bash
   heroku run flask db upgrade
   ```

6. **Initialize Database**
   ```bash
   heroku run flask init-db
   ```

7. **Create Pool Record** (if needed)
   ```bash
   heroku run flask shell
   >>> from app import db
   >>> from app.models import Pool
   >>> pool = Pool(id=1, name='March Madness 2026')
   >>> db.session.add(pool)
   >>> db.session.commit()
   >>> exit()
   ```

---

## 6. Recommended Improvements for 2026

### High Priority

1. **Automated Standings Updates**
   - Add a cron job or scheduler to run standings updates
   - Or trigger automatically after setting winners

2. **Better Error Handling**
   - Add try-catch blocks around critical operations
   - Provide user-friendly error messages

3. **Backup Strategy**
   - Regular database backups
   - Export picks before tournament starts
   - Document rollback procedures

4. **Admin Dashboard**
   - Single page showing:
     - Current standings
     - Pending game updates
     - Recent activity
     - Quick actions

### Medium Priority

1. **Email Notifications**
   - Password reset emails
   - Bracket reminder emails
   - Tournament start notification
   - Daily standings updates

2. **Better Mobile Experience**
   - Simplified bracket entry for mobile
   - Responsive tables
   - Touch-friendly dropdowns

3. **Statistics Page**
   - Most popular picks
   - Biggest upsets
   - Chalk vs. chaos leaderboard
   - Seed performance

4. **Export Functionality**
   - Export brackets to PDF
   - Export standings to CSV
   - Printable brackets

### Low Priority

1. **Real-Time Updates**
   - WebSocket for live standings
   - Live game updates integration
   - Push notifications

2. **Advanced Scoring**
   - Bonus points for upsets
   - Seed-differential scoring
   - Multiple scoring systems

3. **Community Features**
   - User profiles
   - Bracket comparison tool (partially exists)
   - Discussion forum and social interactions
   - User avatars

---

## 7. Quick Reference Commands

### Development
```bash
# Run locally
python run.py

# Run migrations
flask db migrate -m "Migration message"
flask db upgrade

# Initialize database
flask init-db

# Update team names
flask update-team-names
```

### Heroku
```bash
# Deploy
git push heroku main

# Run migrations
heroku run flask db upgrade

# View logs
heroku logs --tail

# Open app
heroku open

# Access database
heroku pg:psql
```

---

## 8. Emergency Procedures

### If Standings Are Wrong

1. Check if `PotentialWinner` table is updated:
   - Navigate to: `/show_potential_winners`
   - Verify potential winners look correct

2. Manually trigger update:
   - Navigate to: Super Admin → Update Potential Winners/Standings
   - Check Admin → View Logs to confirm it ran

3. If still wrong, check game winners:
   - Navigate to: Admin → Set Game Winners
   - Verify all winners are set correctly

### If Users Can't Register

1. Check cutoff time:
   - Navigate to: Admin → Cutoff Status
   - Verify current time vs. cutoff time

2. Check pool configuration:
   - Verify `POOL_ID` environment variable
   - Check if Pool record exists in database

### If Brackets Won't Save

1. Check for JavaScript errors in browser console
2. Verify database connection
3. Check Heroku logs for server errors
4. Verify user authentication

### If Site Is Down

1. Check Heroku status: `heroku ps`
2. Check logs: `heroku logs --tail`
3. Check database: `heroku pg:info`
4. Restart dynos: `heroku restart`

---

## 10. Performance & Algorithm Optimizations

### **A. Core Logic Improvements**

1. **`recalculate_standings()`** [COMPLETED ✅]
   - **Issue**: Performed ~60 database queries per user and committed to the database inside the loop. For 200 users, this was ~12,600 queries and 200 disk writes.
   - **Fix**: Implemented `joinedload` for eager fetching and moved `db.session.commit()` outside the loop.
   - **Status**: [x] Optimized

2. **`get_potential_picks()`** [COMPLETED ✅]
   - **Issue**: Used recursive database queries for every game (63 times) every time the bracket page loaded.
   - **Fix**: Replaced recursion with an in-memory lookup using pre-fetched `games_dict` and `user_picks`. Added internal request caching to prevent redundant calculations.
   - **Status**: [x] Optimized

3. **`set_is_bracket_valid()`** [COMPLETED ✅]
   - **Issue**: Performed multiple database queries per game (up to 180+ queries) during the save process to verify bracket logic.
   - **Fix**: Refactored to use in-memory dictionaries for games and picks, reducing DB access to a single initial fetch.
   - **Status**: [x] Optimized

4. **`admin_analytics()`** [COMPLETED ✅]
   - **Issue**: Loaded the entire `LogEntry` table into a Pandas DataFrame for processing rather than using SQL aggregation.
   - **Fix**: Implemented a single SQL query using `func.date_trunc`, `func.timezone`, and `GROUP BY` to perform all calculations in the database.
   - **Status**: [x] Optimized

### **B. Logic & Bug Fixes**

1. **Cascade Winner Clearing** [COMPLETED ✅]
   - **Issue**: Clearing or changing a game winner only updates the immediate next round. Future rounds (e.g., if a team was already set as the winner of the Sweet 16 and you clear their Round 1 win) remain unchanged, leading to "ghost winners" and incorrect scores.
   - **Fix**: Implemented `clear_team_from_future_games` (recursive) and `advance_team_to_next_game` (slot-aware) helpers.
   - **Status**: [x] Fixed

---

## 11. Appendix A: Database Schema Overview

### User Table
- Stores authentication, scores, tiebreakers, verification status
- Links to Pool via `pool_id`

### Pool Table
- Allows multiple separate pools
- Simple: just `id` and `name`

### Region Table (4 records)
- East, West, South, Midwest (names can be changed yearly)

### Team Table (64 records)
- Each team has seed (1-16), name, and region_id
- IDs 1-16 are Region 1, 17-32 are Region 2, etc.

### Round Table (6 records)
- Each round has name and point value
- IDs are fixed: 1=First Round, 2=Second Round, etc.

### Game Table (63 records)
- Represents each game in tournament
- `team1_id` and `team2_id` are NULL for future rounds initially
- `winning_team_id` is set by admin as tournament progresses
- `winner_goes_to_game_id` links games in bracket structure

### Pick Table
- User's selection for each game
- One record per user per game
- `team_id` references which team they picked

### PotentialWinner Table
- Cache of possible winners for each game
- Comma-separated list of team IDs
- Updated when game winners change
- Used for calculating max possible scores

### LogEntry Table
- Audit trail of all actions
- Links to user who performed action
- Categorized by action type

### Thread & Post Tables
- Simple message board functionality
- Threads can be hidden by admin
- Posts can be hidden by admin

---

## Appendix B: URL Map

### Public URLs
- `/` - Home/redirect
- `/register` - User registration
- `/login` - User login
- `/logout` - User logout
- `/reset_password_request` - Password reset (with code)
- `/reset_password/<user_id>` - Set new password

### User URLs (logged in)
- `/make_picks` - Fill out bracket (before cutoff)
- `/view_picks/<user_id>` - View any user's bracket
- `/standings` - Current standings
- `/user/<user_id>` - User profile
- `/users` - List all users
- `/message_board` - Forum
- `/create_thread` - New forum thread
- `/thread/<thread_id>` - View thread
- `/winners` - Past winners
- `/simulate_standings` - Simulate future scenarios
- `/compare_brackets` - Compare two brackets

### Admin URLs
- `/admin/users` - User status overview
- `/admin/verify_users` - Mark users as verified
- `/admin/view_logs` - Audit log
- `/admin/analytics` - Log analytics
- `/admin/set_winners` - Set game winners
- `/admin/reset_password` - Admin reset user password
- `/admin/reset_password_code` - Generate reset code
- `/admin/manage_regions` - Edit region names
- `/admin/manage_teams` - Edit team names
- `/admin/manage_rounds` - Edit round point values
- `/admin/cutoff_status` - View cutoff time info

### Super Admin URLs
- `/super_admin/manage_admins` - Promote/demote admins
- `/super_admin/reset_games` - Reset game table
- `/super_admin/delete_user` - Delete a user
- `/admin/update_potential_winners` - Trigger standings update

---

## Appendix C: File Structure

```
.
├── app/
│   ├── __init__.py           # App initialization, CLI commands
│   ├── routes.py             # All URL routes
│   ├── models.py             # Database models
│   ├── forms.py              # WTForms definitions
│   ├── utils.py              # Utility functions (cutoff time)
│   ├── static/
│   │   ├── styles.css        # Main stylesheet
│   │   ├── game_grid.css     # Bracket grid styles
│   │   ├── hero.css          # Landing page styles
│   │   ├── games.csv         # Bracket structure definition
│   │   └── winners.csv       # Historical winners
│   └── templates/
│       ├── base.html         # Base template
│       ├── make_picks.html   # Bracket entry
│       ├── view_picks.html   # Bracket viewing
│       ├── standings.html    # Standings table
│       └── [other templates]
├── migrations/               # Database migrations
├── config.py                 # Configuration
├── requirements.txt          # Python dependencies
├── runtime.txt               # Python version (Heroku)
├── Procfile                  # Heroku process definition
└── run.py                    # Application entry point
```

Good luck with your 2026 pool! 🏀
