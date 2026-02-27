from datetime import datetime
import pytz

EASTERN = pytz.timezone('US/Eastern')

# Update each season. Round 0 = First Four (play-in). Rounds 1-6 = bracket.
# All dates are Eastern. End date includes +1 day buffer for games that run past midnight.
# ESPN returns event dates in UTC; we convert to Eastern before comparing.
TOURNAMENT_ROUND_DATES = {
    0: (datetime(2026, 3, 17), datetime(2026, 3, 19)),   # First Four (Tue-Wed) + buffer
    1: (datetime(2026, 3, 19), datetime(2026, 3, 21)),   # 1st Round (Thu-Fri) + buffer
    2: (datetime(2026, 3, 21), datetime(2026, 3, 23)),   # 2nd Round (Sat-Sun) + buffer
    3: (datetime(2026, 3, 26), datetime(2026, 3, 28)),   # Sweet 16 + buffer
    4: (datetime(2026, 3, 28), datetime(2026, 3, 30)),   # Elite 8 + buffer
    5: (datetime(2026, 4, 4), datetime(2026, 4, 5)),      # Final 4
    6: (datetime(2026, 4, 6), datetime(2026, 4, 7)),     # Championship + buffer
}

def is_after_cutoff():
    cutoff_time = get_cutoff_time()
    current_time = get_current_time()
    is_after_cutoff = current_time >= cutoff_time

    return is_after_cutoff

def get_cutoff_time():
    naive_cutoff_time = datetime(2026, 3, 19, 12, 10)  # Naive datetime object (no timezone)
    cutoff_time = EASTERN.localize(naive_cutoff_time)  # Localize to Eastern Time
    return cutoff_time

def get_current_time():
    current_time = datetime.now(EASTERN)  # Current time in Eastern Time
    return current_time
