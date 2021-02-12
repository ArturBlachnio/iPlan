from mymonth import db
import pandas as pd
from datetime import datetime, timedelta
from mymonth.utils import string_from_duration, duration_from_string
import os

df = pd.read_sql_table('days', db.engine)

df = pd.read_excel(os.path.join('mymonth', 'static', 'initial_data', 'import_me.xlsx'))
# Change columns type from string to timedelta (stored as datetime)
for col in ['ds', 'dev', 'pol', 'ge', 'crt', 'hs']:
    df[col] = df[col].fillna('').apply(duration_from_string)

for i, serie in df.iterrows():
    day = f"Days(id={serie['id']}, ds={serie['ds']}, dev={serie['dev']}, pol={serie['pol']}, ge={serie['ge']}, crt={serie['crt']}, hs={serie['hs']}, alk={serie['alk']})"
    print(day)





