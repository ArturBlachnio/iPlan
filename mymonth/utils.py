from calendar import monthrange
from datetime import date


def get_month_first_and_last_day(reference_date):
    """Returns first and last day of a month the reference_date belongs to."""
    first_day = date(year=reference_date.year, month=reference_date.month, day=1)
    last_day = date(year=reference_date.year, month=reference_date.month, day=monthrange(year=reference_date.year, month=reference_date.month)[1])
    return first_day, last_day


def get_all_days_of_month(reference_date):
    """Returns all days in a month (to be used as index in table)."""
    month_start, month_end = get_month_first_and_last_day(reference_date)
    days_in_month = (month_end - month_start).days + 2
    list_of_days = [date(year=month_start.year, month=month_start.month, day=day) for day in range(1, days_in_month)]
    return list_of_days
