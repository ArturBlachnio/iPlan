from datetime import timedelta


class Defaults:
    @staticmethod
    def productive_hours_by_weekday(input_date):
        """ Calculates number of productive hours per weekday. Returns timedelta object.
        Default settings: Saturday (5) and Sunday (6) get 4hrs, rest (0-4) 2hrs"""
        weekday_nb = input_date.weekday()
        dict_productive_hours_per_weekday = {0: 2, 1: 2, 2: 2, 3: 2, 4: 2, 5: 4, 6: 4}
        return timedelta(hours=dict_productive_hours_per_weekday.get(weekday_nb))
