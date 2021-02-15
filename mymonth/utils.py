from calendar import monthrange
from datetime import date, timedelta, datetime
import re
from pandas import NaT

def get_month_days(reference_date):
    """Returns: first, last and all days of a month of reference date."""
    first_day = date(year=reference_date.year, month=reference_date.month, day=1)
    last_day = date(year=reference_date.year, month=reference_date.month, day=monthrange(year=reference_date.year, month=reference_date.month)[1])
    days_in_month = (last_day - first_day).days + 1
    all_days = [date(year=first_day.year, month=first_day.month, day=day) for day in range(1, days_in_month + 1)]
    return first_day, last_day, all_days


def duration_from_string(x):
    """ Converts string to valid datatime.timedelta
    Valid string format examples: 3d, 10h 5m, 1h 3s, 30m2s, etc
    - Each value must be followed by d-day, h-hour, m-minute, s-second
    - Sequence is not important: 1h 30m = 30m 1h
    """
    if x is None:
        return timedelta(0)

    # Dict of period: value pairs: {'h': '3', 'd': '4', 'm': '30', 's': '22'}
    duration_dict = dict(zip(re.findall('[dhms]', x), re.findall('\d+', x)))
    days = int(duration_dict.get('d', 0))
    hours = int(duration_dict.get('h', 0))
    minutes = int(duration_dict.get('m', 0))
    seconds = int(duration_dict.get('s', 0))
    return timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)


def string_from_duration(x):
    """ Converts datatime.timedelta into string
    Function is used to update plan and actual of task model
    """
    # Convert to timedelta if instance of datetime (in mymonth db, intervals are kept as datetime objects starting at 1970-1-1)
    if isinstance(x, datetime):
        x = x - datetime(1970, 1, 1)
    
    if x is None or x is NaT or x.total_seconds() == 0:
        return ''

    total_seconds = x.total_seconds()
    days = total_seconds // 86400
    total_seconds -= days * 86400
    hours = total_seconds // 3600
    total_seconds -= hours * 3600
    minutes = total_seconds // 60
    total_seconds -= minutes * 60
    seconds = total_seconds

    # Compact display: if nb of none-zero items > 2 than drop seconds.
    duration_items = [(days, 'd'), (hours, 'h'), (minutes, 'm'), (seconds, 's')]
    non_zero_items = 0
    for item in duration_items:
        if item[0] != 0:
            non_zero_items += 1

    if non_zero_items > 2:
        duration_items.pop(-1)

    # Final output
    outcome = ''
    for item in duration_items:
        if item[0] != 0:
            outcome += f'{int(item[0])}{item[1]} '
    return outcome[:-1]

def string_from_float(x):
    outcome = x
    if x is None:
        outcome = ''
    return outcome

def float_from_string(x):
    outcome = x
    if x == '':
        outcome = None
    elif isinstance(x, str):
        outcome = outcome.replace(',', '.')
    return outcome

def get_target_productive_hours_per_day(input_date):
    """ Calculates number of productive hours per day. Returns timedelta object"""
    weekday_nb = input_date.weekday()
    dict_productive_hours_per_weekday = {0: 2, 1: 2, 2: 2, 3: 2, 4: 2, 5: 4, 6: 4}  # Saturday (5) and Sunday (6) get 4hrs, rest (0-4) 2hrs
    return timedelta(hours=dict_productive_hours_per_weekday.get(weekday_nb))
