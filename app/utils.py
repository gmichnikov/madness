from datetime import datetime
import pytz

EASTERN = pytz.timezone('US/Eastern')

def is_after_cutoff():
    cutoff_time = get_cutoff_time()
    current_time = get_current_time()
    is_after_cutoff = current_time >= cutoff_time

    return is_after_cutoff

def get_cutoff_time():
    naive_cutoff_time = datetime(2024, 3, 21, 12, 10)  # Naive datetime object (no timezone)
    cutoff_time = EASTERN.localize(naive_cutoff_time)  # Localize to Eastern Time
    return cutoff_time

def get_current_time():
    current_time = datetime.now(EASTERN)  # Current time in Eastern Time
    return current_time
