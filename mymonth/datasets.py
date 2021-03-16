"""Module contains:
 - DataBase (db) queries and their outputs,
 - Datasets that are displayed in routes
"""
from datetime import date


def get_day_of_month_for_avg_sja(month_start_date, month_end_date):
    # todo - datasets (it's only used for days statistics)
    """Returns day of month that is used to divide SJA to get average monthly consumption.
    If month was in the past - get last day of given month. If month is in the future - get first day of given month."""
    # If in current month
    if month_start_date <= date.today() <= month_end_date:
        day_counter = date.today().day
    elif date.today() > month_end_date:
        day_counter = month_end_date.day
    else:
        day_counter = month_start_date.day
    return day_counter
