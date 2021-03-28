import pandas as pd
from mymonth.datasets import DataSet
from datetime import datetime

ds = DataSet()

df = ds.tracking_df_daily_datetime

df[df.index < datetime.today()]