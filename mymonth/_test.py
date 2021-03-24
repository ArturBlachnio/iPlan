from mymonth import db
import pandas as pd
from artools.utils import show_attributes
from datetime import datetime, timedelta
pd.options.display.expand_frame_repr = False
pd.options.display.min_rows = 31
from mymonth.models import MonthlyTargets

# todo - in classs make function returning sql_queries based on input time

sql_query = "SELECT * FROM Days WHERE id between '2021-03-01' and '2021-03-31'"
parse_dates = ['id', 'ds', 'dev', 'pol', 'ge', 'crt', 'hs']
df = pd.read_sql_query(sql=sql_query, con=db.engine, index_col='id', parse_dates=parse_dates)

df['days0'] = 0
datetime_columns = df.select_dtypes(include='datetime').columns
float_columns = df.select_dtypes(include='number').columns

# Change NaN/NaT into zeros
df[float_columns] = df[float_columns].fillna(0)
df[datetime_columns] = df[datetime_columns].fillna(datetime(1970, 1, 1))

# Convert datetimes (dtype used in db to keep intervals) to timedeltas
df[datetime_columns] = df[datetime_columns] - datetime(1970, 1, 1)
df['days0'] = (df.alk == 0).astype(int)

# Add cummulative sums to datetime columns
df[datetime_columns] = df[datetime_columns].cumsum()
df[float_columns] = df[float_columns].cumsum()


# Targets dataset
sql_query_targets = "SELECT * FROM monthly_targets WHERE id == '2021-03-01'"
tg = pd.read_sql_query(sql=sql_query_targets, con=db.engine, index_col='id', parse_dates=parse_dates)
tg[datetime_columns] = tg[datetime_columns] - datetime(1970, 1, 1)

tg = tg/df.shape[0]
tg = tg.reindex(df.index, method='ffill').cumsum()
tg
df
tg.ds.dt.days

sc = df - tg

# Show deltas in hours
for column in datetime_columns:
    sc[column] = sc[column].dt.total_seconds()/3600

# todo change alk to proper sja (not cumm or translate that into mls)
sc

score.info()
score.dev.dt.total_seconds()


# replace

# Add targets
# Add cumsum to targets
# Add difference
# put that on the graph

df
df.ds.cumsum()
df.info()