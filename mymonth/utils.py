from calendar import monthrange
from datetime import date, timedelta, datetime
import re
import pandas as pd
import numpy as np
import os

from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import ColumnDataSource, NumeralTickFormatter, LinearAxis, Range1d, LabelSet, DatetimeTickFormatter, BoxAnnotation

def get_month_days(reference_date):
    """Returns: first, last and all days of a month of reference date."""
    first_day = date(year=reference_date.year, month=reference_date.month, day=1)
    last_day = date(year=reference_date.year, month=reference_date.month, day=monthrange(year=reference_date.year,
                                                                                         month=reference_date.month)[1])
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


def string_from_duration(x, output_format=None):
    """ Converts datatime.timedelta into string
    Function is used to update plan and actual of task model
    """
    # Convert to timedelta if instance of datetime (in mymonth db, intervals are kept as datetime objects starting at
    # 1970-1-1)
    if isinstance(x, datetime):
        x = x - datetime(1970, 1, 1)

    if x is None or x is pd.NaT or x.total_seconds() == 0:
        return ''

    if output_format == 'hm':
        total_seconds = x.total_seconds()
        hours = total_seconds // 3600
        total_seconds -= hours * 3600
        minutes = total_seconds // 60
        return f'{int(hours)}h {int(minutes)}m'

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
    dict_productive_hours_per_weekday = {0: 2, 1: 2, 2: 2, 3: 2, 4: 2, 5: 4,
                                         6: 4}  # Saturday (5) and Sunday (6) get 4hrs, rest (0-4) 2hrs
    return timedelta(hours=dict_productive_hours_per_weekday.get(weekday_nb))


def get_day_of_month_for_avg_sja(month_start_date, month_end_date):
    """Returns day of month that is used to devide SJA to get average monthly consumption. 
    If month was in the past - get last day of given month. If month is in te future - get first day of given month. """
    # If in current month
    if month_start_date <= date.today() <= month_end_date:
        day_counter = date.today().day
    elif date.today() > month_end_date:
        day_counter = month_end_date.day
    else:
        day_counter = month_start_date.day
    return day_counter


def calc_proper_timedelta_difference(timedelta_1, timedelta_2):
    """Returns proper timedelta between 2 timedelta object. 
    It's needed for subtracting bigger from smaller timedelta (inbuilt function does something strange)"""
    delta_seconds = timedelta_1.total_seconds() - timedelta_2.total_seconds()

    output_str = string_from_duration(timedelta(seconds=abs(delta_seconds)))

    if delta_seconds < 0:
        output_str = f"-{output_str}"

    return output_str


def transform_historical_scores_into_daily_data(input_path, input_sheetname):
    """Data from the past are available only at aggregated levels. This function transforms it into standards daily
    recodes that will be used to produce monthly summaries. """

    # Load historical data from excel file
    df_historical = pd.read_excel(input_path, sheet_name=input_sheetname)
    df_historical.dropna(inplace=True)
    df_historical['date'] = pd.to_datetime(df_historical['month'], format='%ym%m')
    df_historical.set_index('date', inplace=True)

    # Reindexing with all days in each month
    list_of_indexes = [get_month_days(item)[2] for item in df_historical.index]
    new_index = []
    for list_item in list_of_indexes:
        new_index.extend(list_item)
    df = df_historical.reindex(new_index, method='ffill').reset_index()

    # Recalculation of day0 and ml
    count_days_in_month = df.groupby('month').size()
    count_days_in_month.name = 'nb_of_days'
    df = df.merge(count_days_in_month, how='left', on='month')
    df['new_ml'] = df.ml * df.nb_of_days / (df.nb_of_days - df.day0)

    df_groups = []
    for group_name, group_data in list(df.groupby('month')):
        nb_days0 = group_data.day0.iloc[0]
        ml_including_days0 = group_data.new_ml.copy()
        ml_including_days0.iloc[0: nb_days0] = 0
        group_data['new_ml'] = ml_including_days0
        df_groups.append(group_data)
    df = pd.concat(df_groups, ignore_index=True)

    # Calculation of Sja and negative hours
    df['sja'] = df.new_ml * 7.8 / 750
    df['negative_hrs'] = (df['sja'] - 2.86).clip(0) * timedelta(minutes=20)

    # Calculation of productive hours taking into account negative time from sja
    df['target_hrs'] = df['date'].map(get_target_productive_hours_per_day)
    df_positive_hrs_calc = df.groupby('month', as_index=False)[
        ['negative_hrs', 'target_hrs', 'score', 'nb_of_days']].agg(
        {'negative_hrs': sum, 'target_hrs': sum, 'score': np.mean, 'nb_of_days': max})
    df_positive_hrs_calc['avg_positive_hrs'] = (df_positive_hrs_calc['target_hrs'] * df_positive_hrs_calc['score'] +
                                                df_positive_hrs_calc['negative_hrs']) / df_positive_hrs_calc[
                                                   'nb_of_days']
    df = df.merge(df_positive_hrs_calc[['month', 'avg_positive_hrs']], how='left', on='month')

    # Reshape and rename df to match input of daily activities - All set to 'dev' category
    df_import_me = df[['date', 'avg_positive_hrs', 'sja']].copy()
    df_import_me.rename(columns={'date': 'id', 'avg_positive_hrs': 'dev', 'sja': 'alk'}, inplace=True)
    df_import_me['dev'] = df_import_me['dev'].map(string_from_duration)
    df_import_me['id'] = pd.to_datetime(df_import_me['id'])
    return df_import_me


def get_initial_data_from_excel(input_path=os.path.join('mymonth', 'static', 'initial_data', 'import_me.xlsx')):
    """Gets historical data from excel file.
    Combines 2 worksheets:
     - 'days' with historical data based recorded on daily levels, and
     - 'historical_scores' with scores and alk aggregated to months. """

    # Load data from excel
    df_days = pd.read_excel(input_path, sheet_name='days')
    df_historical_scores = transform_historical_scores_into_daily_data(input_path=input_path,
                                                                       input_sheetname='historical_scores')

    # Concatenate and drop duplicates (keep first entries - details of days have priority over months)
    df = pd.concat([df_days, df_historical_scores], ignore_index=True)
    df.drop_duplicates(subset='id', inplace=True)

    return df


class MonthlyGraph:
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
        """Returns dataframe with all entries between:
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
