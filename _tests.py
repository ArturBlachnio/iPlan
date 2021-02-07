from mymonth import db
from mymonth.models import Days
from datetime import date, timedelta
from calendar import monthrange
import pandas as pd 


db.create_all()
day8 = Days(id=date(2021, 2, 8), dev=timedelta(seconds=345), alk=3.8)
day20 = Days(id=date(2021, 2, 20), ge=timedelta(seconds=1000), alk=7.8)
day31 = Days(id=date(2021, 3, 10), dev=timedelta(seconds=1000), alk=7.8)
day41 = Days(id=date(2021, 3, 20), ge=timedelta(seconds=1000), alk=3.8)
db.session.add(day8)
db.session.add(day20)
db.session.add(day31)
db.session.add(day41)
db.session.commit()

output = Days.query.all()

reference_date = date(2021, 2, 10)
month_start = date(year=reference_date.year, month=reference_date.month, day=1)
month_end = date(year=reference_date.year, month=reference_date.month, day=monthrange(year=reference_date.year, month=reference_date.month)[1])
pd.date_range(month_start, month_end)



get_all_days_of_month(date(2021,2,1))

get_month_atributes(date(2021, 3, 31))

output = Days.query.filter(Days.id >= month_start).filter(Days.id <= month_end).all()

df = pd.read_sql_table('days', db.engine)
qry = f"SELECT * FROM days WHERE id BETWEEN '{month_start.isoformat()}' and '{month_end.isoformat()}'"
df = pd.read_sql_query(qry, db.engine, parse_dates=['id'])
df = df.set_index('id').reindex(pd.date_range(month_start, month_end))


df.fillna(999)


for i in output:
    print(i)