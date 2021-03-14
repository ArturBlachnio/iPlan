import os
import pandas as pd
import numpy as np
from mymonth.utils import UtilsDatetime, UtilsDataConversion
from mymonth.utils import get_target_productive_hours_per_day
from datetime import timedelta


def transform_historical_scores_into_daily_data(input_path, input_sheetname):
    """Data from the past are available only at aggregated levels. This function transforms it into standards daily
    recodes that will be used to produce monthly summaries. """

    # Load historical data from excel file
    df_historical = pd.read_excel(input_path, sheet_name=input_sheetname)
    df_historical.dropna(inplace=True)
    df_historical['date'] = pd.to_datetime(df_historical['month'], format='%ym%m')
    df_historical.set_index('date', inplace=True)

    # Reindexing with all days in each month
    list_of_indexes = [UtilsDatetime(day).month_all_dates for day in df_historical.index]
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
    df_import_me['dev'] = df_import_me['dev'].map(UtilsDataConversion.string_from_timedelta)
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
