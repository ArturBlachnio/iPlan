"""Module contains:
 - DataBase (db) queries and their outputs,
 - Datasets that are displayed in routes
"""
from datetime import date, datetime
import pandas as pd
from mymonth import db
from mymonth.utils import UtilsDatetime

pd.options.display.expand_frame_repr = False
pd.options.display.min_rows = 31


class DataSet:
    """
    A class used to easily query database. Contains predefines queries
    and methods to extract and convert data using pandas DataFrame.
    """
    db_connection = db.engine

    def __init__(self, month_reference_date=None):
        """
        Parameters
        ----------
        month_reference_date : datetime (default is today)
            The reference date that is used to determine query period, if applicable.
        """
        if month_reference_date is None:
            self.month_reference_date = date.today()
        else:
            self.month_reference_date = month_reference_date

        # Attributes of days table
        self.days_table_name = 'days'
        self.days_query_columns_datetime = ['id', 'ds', 'dev', 'pol', 'ge', 'crt', 'hs']
        self.days_query_columns_float = ['alk']

        # Attributes of monthly_targets table
        self.targets_table_name = 'monthly_targets'
        self.targets_query_columns_datetime = ['id', 'ds', 'dev', 'pol', 'ge', 'crt', 'hs']
        self.targets_query_columns_float = ['alk']

        # Attributes of tracking table
        self.tracking_columns_datetime = ['ds', 'dev', 'pol', 'ge', 'crt', 'hs']

        # Database raw tables preprocessed
        self.days_df_datetime = self.create_days_df_datetime()
        self.days_df_numeric = None
        self.targets_df_datetime = self.create_df_targets_datetime()
        self.targets_df_numeric = None

        # Tracking tables
        self.tracking_df_daily_datetime = self.create_tracking_df_daily_datetime()
        self.tracking_df_daily_numeric = None

    def get_sql_statement(self, table, columns=None, use_reference_date=False, filter_dates_column='id',
                          start_date=None, end_date=None):
        """Returns sql_query that will be get data from database with pandas read_sql_query.

        Parameters
        ----------
        table : string
            Name of a table in database.
        columns : list, optional
            Columns passed to SELECT statement (default is None).
            If None, all columns are passed ('SELECT *').
        use_reference_date : bool (default is False)
            Month Reference date will be used to generate first and last day of query period.
            If False: all dates are used.
        filter_dates_column : str (default is id)
            Name of column to WHERE statement applies.
        start_date : date (default is None)
            First selection date.
        end_date : date (default is None)
            Last selection date.
        """
        if columns is None:
            columns = '*'
        elif isinstance(columns, (list, tuple)):
            columns = ', '.join(columns)

        if use_reference_date:
            udt = UtilsDatetime(self.month_reference_date)
            start_date = udt.month_first_date.isoformat()
            end_date = udt.month_last_date.isoformat()

        if start_date is not None and end_date is not None:
            where_statement = f'WHERE {filter_dates_column} BETWEEN "{start_date}" AND "{end_date}"'
        elif start_date is not None and end_date is None:
            where_statement = f'WHERE {filter_dates_column} >= "{start_date}"'
        elif start_date is None and end_date is not None:
            where_statement = f'WHERE {filter_dates_column} <= "{end_date}"'
        else:
            where_statement = ''
        return f'SELECT {columns} FROM {table} {where_statement}'

    @staticmethod
    def _format_df_with_timedelta(input_df):
        """Formats and cleans dataframe with only datetime columns"""
        # Change NaN/NaT into zeros
        input_df.fillna(datetime(1970, 1, 1), inplace=True)
        # Convert datetimes (data type used in db to keep intervals) to timedeltas
        input_df = input_df - datetime(1970, 1, 1)
        return input_df

    def create_days_df_datetime(self):
        """Returns and cleans datetime columns from table days"""
        sql_query = self.get_sql_statement(self.days_table_name, columns=self.days_query_columns_datetime,
                                           use_reference_date=True)
        df = pd.read_sql_query(sql=sql_query, con=self.db_connection,
                               index_col='id', parse_dates=self.days_query_columns_datetime)
        df = self._format_df_with_timedelta(df)
        return df

    def create_df_targets_datetime(self):
        """Returns and cleans datetime columns from table monthly_targets"""
        sql_query = self.get_sql_statement(self.targets_table_name, columns=self.targets_query_columns_datetime,
                                           use_reference_date=True)
        df = pd.read_sql_query(sql=sql_query, con=self.db_connection,
                               index_col='id', parse_dates=self.targets_query_columns_datetime)
        df = self._format_df_with_timedelta(df)
        return df

    def create_tracking_df_daily_datetime(self):
        """Returns dataset to display hours spend vs targets on a daily level"""
        actuals = self.days_df_datetime.cumsum()
        # Reindex targets and get cumulative values
        targets = self.targets_df_datetime / actuals.shape[0]
        targets = targets.reindex(actuals.index, method='ffill').cumsum()
        df = actuals - targets
        # Convert output to hours
        for column in self.tracking_columns_datetime:
            df[column] = df[column].dt.total_seconds()/3600
        # Add total column
        df['total'] = df.sum(axis=1)
        return df



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
