from mymonth.models import Days, Settings
from artools.utils import show_attributes
from mymonth.utils import get_month_days
from datetime import date, timedelta
from mymonth import db
import pandas as pd
import numpy as np

REF_DATE = Settings.query.first().current_month_date
REF_DATE


class MonthlyGraph:
    def __init__(self, db_table):
        self.db_table = db_table
        self.historical_data = self.get_historical_data_from_db()
        self.df = self.convert_days_model_to_dataframe(self.historical_data)

    def get_historical_data_from_db(self, reference_date=None, display_years=2):
        """Returns dataframe with all entries between:
         - last day of previous month (selection=reference_date), and:
         - first day of current year - 'display_years'."""

        if reference_date is None:
            reference_date = date.today()

        query_last_date = date(reference_date.year, reference_date.month, 1) - timedelta(days=1)
        query_first_date = date(reference_date.year - display_years, 1, 1)
        query_output = self.db_table.query.filter(Days.id.between(query_first_date, query_last_date)).all()
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

        # Fill nans
        columns_numerical = df.select_dtypes(include=['float64', 'int']).columns
        columns_timedelta = df.select_dtypes(include=['timedelta']).columns
        df[columns_timedelta] = df[columns_timedelta].fillna(timedelta())
        df[columns_numerical] = df[columns_numerical].fillna(0)
        return df


mg = MonthlyGraph(Days)

mg.df
