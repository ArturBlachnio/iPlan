"""Module contains:
 - Utilities (combined into classes) and can be used across all modules
"""
from calendar import monthrange
from datetime import date, timedelta, datetime
import re
from pandas import NaT


class UtilsDatetime:
    """Tools related to datetime objects"""
    def __init__(self, input_date):
        self.date = input_date
        self.month = input_date.month
        self.year = input_date.year

    @property
    def month_first_date(self):
        """Returns first day of a month representing input_date"""
        return date(year=self.year, month=self.month, day=1)

    @property
    def month_last_date(self):
        """Returns last day of a month representing input_date"""
        last_day = monthrange(year=self.year, month=self.month)[1]
        return date(year=self.year, month=self.month, day=last_day)

    @property
    def month_all_dates(self):
        """Returns all days of a month as a list"""
        number_days_in_month = (self.month_last_date - self.month_first_date).days + 1
        return [date(year=self.year, month=self.month, day=day) for day in range(1, number_days_in_month + 1)]


class UtilsDataConversion:
    """Tools related to converting data types"""
    @staticmethod
    def timedelta_from_string(input_string):
        """ Converts string into timedelta object
        Valid string format examples: 3d, 10h 5m, 1h 3s, 30m2s, etc
        - Each value must be followed by d-day, h-hour, m-minute, s-second
        - Sequence is not important: 1h 30m = 30m 1h
        """
        if input_string is None:
            return timedelta(0)

        # Dict of period: value pairs: {'h': '3', 'd': '4', 'm': '30', 's': '22'}
        duration_dict = dict(zip(re.findall('[dhms]', input_string), re.findall(r'\d+', input_string)))
        days = int(duration_dict.get('d', 0))
        hours = int(duration_dict.get('h', 0))
        minutes = int(duration_dict.get('m', 0))
        seconds = int(duration_dict.get('s', 0))
        return timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

    @staticmethod
    def string_from_timedelta(input_timedelta, output_format=None, show_units_with_zero=False):
        """ Converts timedelta object into string e.g. 2h 35m with a specified output_format.
         - input_timedelta: must be timedelta object.
           If gives as datetime, will be converted to timedelta.
           If empty, None or equal to 0 seconds, will return empty string ''.
         - output_format: (default = 'd h m s') accepts combinations of 'd'-days, 'h'-hours, 'm'-minutes and 's'-secs.
           Format examples: 'd hh m' or 'h mm ss'.
           Double unit like 'hh' ensures displaying value as 2-digit. '2h' with 'hh' returns '02h'.
           Spaces in format are taken into account. Use 'hmm' to show '1h33m', 'h mm' for '1h 33m'.
         - show_units_with_zeros: (default = False) forces displaying '0d' or '00h' if value for unit equals zero.

        """
        # If input_timedelta is datetime. In database intervals are kept as datetime objects starting at 1970-1-1)
        if isinstance(input_timedelta, datetime):
            input_timedelta = input_timedelta - datetime(1970, 1, 1)

        if input_timedelta is None or input_timedelta is NaT or input_timedelta.total_seconds() == 0:
            return ''

        input_timedelta = input_timedelta.total_seconds()

        # Set default output format
        if output_format is None:
            output_format = 'd h m s'
        # Translate format from string to dict of {time_indicator: {'digits': X, 'rest': Y}
        # E.g.  'd hh mm' -> {'d': {'digits': 1, 'rest': ' '}, 'h': {'digits': 2, 'rest': ' '}, [...]}
        seconds_per_unit = {'d': 86400, 'h': 3600, 'm': 60, 's': 1}
        output_format_attrs = {}
        for unit in seconds_per_unit:
            output_format_attrs[unit] = {'digits': 0, 'rest': ''}
            unit_presence = re.findall(rf'{unit}+\s*', output_format)
            if unit_presence:
                output_format_attrs[unit]['digits'] = unit_presence[0].count(unit)
                output_format_attrs[unit]['rest'] = unit_presence[0].replace(unit, '')

        output_string = ''
        for unit in output_format_attrs:
            if output_format_attrs[unit]['digits'] > 0:
                unit_value = int(input_timedelta // seconds_per_unit[unit])
                if unit_value > 0 or (unit_value == 0 and show_units_with_zero):
                    input_timedelta -= unit_value * seconds_per_unit[unit]
                    output_string += f"{unit_value:0>{output_format_attrs[unit]['digits']}}{unit}" \
                                     f"{output_format_attrs[unit]['rest']}"
        return output_string.strip()

    @staticmethod
    def string_from_timedelta_subtraction(timedelta_1, timedelta_2):
        """Returns proper timedelta between 2 timedelta object.
        It's needed to subtract bigger from smaller timedelta (inbuilt function does something strange)"""
        delta_seconds = timedelta_1.total_seconds() - timedelta_2.total_seconds()
        output_str = UtilsDataConversion.string_from_timedelta(timedelta(seconds=abs(delta_seconds)))
        if delta_seconds < 0:
            output_str = f"-{output_str}"
        return output_str

    @staticmethod
    def string_from_float_none(input_float):
        """Converts None value (when data type is float) into empty string ''. """
        if input_float is None:
            input_float = ''
        return input_float

    @staticmethod
    def float_from_string(input_string):
        """Converts string with number into data type float."""
        if input_string == '':
            input_string = None
        return input_string

    @staticmethod
    def suffix_to_day_of_month(input_day_number: int = None) -> str:
        if input_day_number is None:
            return ''
        special_suffixed = {'st': [1, 21, 31], 'nd': [2, 22], 'rd': [3, 23]}
        for k, v in special_suffixed.items():
            if input_day_number in v:
                return f'{input_day_number}{k}'
        return f'{input_day_number}th'


mapper_suffix_to_day = {k: UtilsDataConversion.suffix_to_day_of_month(k) for k in range(1, 32)}
