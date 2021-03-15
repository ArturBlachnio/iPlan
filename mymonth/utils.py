"""Module contains:
 - Utilities (combined into classes) and can be used across all modules
"""
from calendar import monthrange
from datetime import date, timedelta, datetime
import re
import pandas as pd

from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import ColumnDataSource, NumeralTickFormatter, LinearAxis, Range1d, LabelSet, DatetimeTickFormatter, BoxAnnotation


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
        duration_dict = dict(zip(re.findall('[dhms]', input_string), re.findall('\d+', input_string)))
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
         - output_format: (default = 'd h m s') accepts combinations of 'd'-days, 'h'-hours, 'm'-minutes and 's'-seconds.
           Format examples: 'd hh m' or 'h mm ss'.
           Double unit like 'hh' ensures displaying value as 2-digit. '2h' with 'hh' returns '02h'.
           Spaces in format are taken into account. Use 'hmm' to show '1h33m', 'h mm' for '1h 33m'.
         - show_units_with_zeros: (default = False) forces displaying '0d' or '00h' if value for unit equals zero.

        """
        # If input_timedelta is datetime. In database intervals are kept as datetime objects starting at 1970-1-1)
        if isinstance(input_timedelta, datetime):
            input_timedelta = input_timedelta - datetime(1970, 1, 1)

        if input_timedelta is None or input_timedelta is pd.NaT or input_timedelta.total_seconds() == 0:
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
            unit_presence = re.findall(f'{unit}+\s*', output_format)
            if unit_presence:
                output_format_attrs[unit]['digits'] = unit_presence[0].count(unit)
                output_format_attrs[unit]['rest'] = unit_presence[0].replace(unit, '')

        output_string = ''
        for unit in output_format_attrs:
            if output_format_attrs[unit]['digits'] > 0:
                unit_value = int(input_timedelta // seconds_per_unit[unit])
                if unit_value > 0 or (unit_value == 0 and show_units_with_zero):
                    input_timedelta -= unit_value * seconds_per_unit[unit]
                    output_string += f"{unit_value:0>{output_format_attrs[unit]['digits']}}{unit}{output_format_attrs[unit]['rest']}"
        return output_string.strip()


def string_from_float(x):
    # todo - UtilsDataConversion - check if model Days default_value set to zero affects it
    outcome = x
    if x is None:
        outcome = ''
    return outcome


def float_from_string(x):
    # todo - UtilsDataConversion - check if model Days default_value set to zero affects it
    outcome = x
    if x == '':
        outcome = None
    elif isinstance(x, str):
        outcome = outcome.replace(',', '.')
    return outcome


def get_target_productive_hours_per_day(input_date):
    # todo - Core? - move to defaults
    """ Calculates number of productive hours per day. Returns timedelta object"""
    weekday_nb = input_date.weekday()
    dict_productive_hours_per_weekday = {0: 2, 1: 2, 2: 2, 3: 2, 4: 2, 5: 4,
                                         6: 4}  # Saturday (5) and Sunday (6) get 4hrs, rest (0-4) 2hrs
    return timedelta(hours=dict_productive_hours_per_weekday.get(weekday_nb))


def get_day_of_month_for_avg_sja(month_start_date, month_end_date):
    # todo - datasets (it's only used for days staristics)
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


def calc_proper_timedelta_difference(timedelta_1, timedelta_2):
    # todo - UtilsDate
    """Returns proper timedelta between 2 timedelta object. 
    It's needed for subtracting bigger from smaller timedelta (inbuilt function does something strange)"""
    delta_seconds = timedelta_1.total_seconds() - timedelta_2.total_seconds()

    output_str = UtilsDataConversion.string_from_timedelta(timedelta(seconds=abs(delta_seconds)))

    if delta_seconds < 0:
        output_str = f"-{output_str}"

    return output_str


class MonthlyGraph:
    # todo - rename and move to graphs.py
    def __init__(self, db_table):
        self.db_table = db_table
        self.db_table_query_output = self.get_historical_data_from_db()
        self.df_days = self.convert_days_model_to_dataframe(self.db_table_query_output)
        self.df_months = self.get_summary_per_month(self.df_days)
        # Append current month summary
        self.df_months = self.df_months.append(self.get_summary_for_current_month())
        # Graph
        self.bokeh_monthly_components = self.get_monthly_graph_components(self.df_months)

    def get_historical_data_from_db(self, reference_date=None, display_years=2):
        # todo - move to datasets
        """Returns DataFrame with all entries between:
         - last day of previous month (selection=reference_date), and:
         - first day of current year - 'display_years'."""

        if reference_date is None:
            reference_date = date.today()

        query_last_date = date(reference_date.year, reference_date.month, 1) - timedelta(days=1)
        query_first_date = date(reference_date.year - display_years, 1, 1)
        query_output = self.db_table.query.filter(self.db_table.id.between(query_first_date, query_last_date)).all()
        return query_output

    @staticmethod
    def convert_days_model_to_dataframe(query_output):
        # todo - move to datasets and make it smarter
        """"Converts 'Days' query output into pandas DataFrame."""
        id = []
        ds = []
        dev = []
        pol = []
        ge = []
        crt = []
        hs = []
        alk = []
        for row in query_output:
            id.append(row.id)
            ds.append(row.ds)
            dev.append(row.dev)
            pol.append(row.pol)
            ge.append(row.ge)
            crt.append(row.crt)
            hs.append(row.hs)
            alk.append(row.alk)
        df = pd.DataFrame(data={'id': id, 'ds': ds, 'dev': dev, 'pol': pol, 'ge': ge, 'crt': crt, 'hs': hs, 'alk': alk})

        df.id = pd.to_datetime(df.id)
        # Fill nans
        columns_numerical = df.select_dtypes(include=['float64', 'int']).columns
        columns_timedelta = df.select_dtypes(include=['timedelta']).columns
        df[columns_timedelta] = df[columns_timedelta].fillna(timedelta())
        df[columns_numerical] = df[columns_numerical].fillna(0)
        return df

    @staticmethod
    def get_summary_per_month(df_days):
        # todo - move to datasets
        """Translates daily data into monthly summary"""
        df_days['month'] = df_days.id.dt.strftime('%ym%m')
        df_days['month_first_day'] = df_days.id
        df_days.alk.fillna(0, inplace=True)
        df_days.loc[(df_days.alk == 0), 'day0'] = 1
        df_days['ml'] = df_days.alk / 7.8 * 750
        df_days['productive_hrs'] = df_days.select_dtypes(include=['timedelta']).sum(axis=1)
        df_days.loc[df_days['productive_hrs'] == 0, 'productive_hrs'] = timedelta()
        df_days['target_hrs'] = df_days.id.map(get_target_productive_hours_per_day)
        df_days['negative_hrs'] = (df_days['alk'] - 2.86).clip(0) * timedelta(minutes=20)

        df_month_score = df_days.groupby('month')[['productive_hrs', 'target_hrs', 'negative_hrs']].sum()
        df_month_score['score'] = (df_month_score.productive_hrs - df_month_score.negative_hrs) / df_month_score.target_hrs
        df_month_alk = df_days.groupby('month')[['day0', 'ml', 'id', 'month_first_day']].agg({'day0': sum, 'ml': sum, 'id': 'count', 'month_first_day': 'first'})
        df_months = df_month_score.join(df_month_alk)
        df_months['ml'] = df_months.ml / df_months.id
        df_months = df_months[['score', 'day0', 'ml', 'month_first_day']]
        return df_months

    def get_summary_for_current_month(self, reference_date=None):
        # todo - move to datasets
        """"Generates summary (score, days0 and ml) for current month"""
        if reference_date is None:
            reference_date = date.today()

        query_last_date = reference_date
        query_first_date = date(reference_date.year, reference_date.month, 1)
        query_output = self.db_table.query.filter(self.db_table.id.between(query_first_date, query_last_date)).all()

        df_days = self.convert_days_model_to_dataframe(query_output)
        df_months = self.get_summary_per_month(df_days)
        return df_months

    @staticmethod
    def get_monthly_graph_components(df_month):
        # todo - move to graphs
        df_month['labels_ml'] = df_month['ml'].astype(int).astype(str)
        df_month['labels_day0'] = df_month['day0'].astype(int).astype(str)
        df_month['ml_current'] = df_month['ml'].values[-1]
        df_month['ml_rank'] = df_month['ml'].rank().astype(int).map({1: '1st', 2: '2nd', 3: '3rd', 4: '4th', 5: '5th'}).fillna('')
        source = ColumnDataSource(df_month)
        plot = figure(title='Monthly summary',
                      x_range=source.data.get('month'),
                      y_range=Range1d(0, max(source.data.get('score')) * 1.1),
                      y_axis_label='Score [%]',
                      plot_width=600,
                      plot_height=400,
                      toolbar_location=None)

        plot.xaxis.major_label_orientation = 1
        plot.yaxis[0].formatter = NumeralTickFormatter(format='0%')

        plot.vbar(x='month', top='score', width=0.8, source=source, color=(100, 149, 237, 0.5), line_width=2)

        plot.extra_y_ranges['y_axis_ml'] = Range1d(0, max(source.data.get('ml')) * 1.05)
        axis_ml = LinearAxis(y_range_name="y_axis_ml", axis_label="Avg ml")
        plot.line(x='month', y='ml_current', y_range_name='y_axis_ml', source=source, line_color='maroon', line_width=0, line_dash='dotted')
        labels_ml_rank = LabelSet(x='month', y='ml', text='ml_rank', y_range_name='y_axis_ml', text_font_size='10px', text_color='gray', x_offset=-7, y_offset=-20, level='annotation', source=source, render_mode='canvas')
        plot.line(x='month', y='ml', y_range_name='y_axis_ml', source=source, line_color='maroon', line_width=2)
        plot.circle(x='month', y='ml', y_range_name='y_axis_ml', source=source, color="maroon", fill_color="white", size=7)
        labels_ml = LabelSet(x='month', y='ml', text='labels_ml', y_range_name='y_axis_ml', text_font_size='10px', text_color='maroon', x_offset=-3, y_offset=7, level='annotation', source=source, render_mode='canvas')

        plot.extra_y_ranges['y_axis_day0'] = Range1d(0, 50)
        plot.line(x='month', y='day0', y_range_name='y_axis_day0', source=source, line_color='gray', line_width=1)
        plot.circle(x='month', y='day0', y_range_name='y_axis_day0', source=source, color="gray", fill_color="white", size=7)
        labels_day0 = LabelSet(x='month', y='day0', text='labels_day0', y_range_name='y_axis_day0', text_font_size='10px', text_color='black', x_offset=-3, y_offset=5, level='annotation', source=source, render_mode='canvas')

        plot.add_layout(axis_ml, 'right')
        plot.add_layout(labels_ml)
        plot.add_layout(labels_day0)
        plot.add_layout(labels_ml_rank)
        return components(plot)
