from datetime import timedelta
from mymonth import db
from mymonth.models import Days, Settings, MonthlyTargets
from artools.utils import show_attributes

show_attributes(Days.query)
show_attributes(db)

import pandas as pd
df = pd.read_excel(os.path.join('mymonth', 'static', 'initial_data', 'import_me.xlsx'))

df.id

# db.create_all()

Settings.query.first() is None:


a = timedelta()

a.total_seconds()

show_attributes(MonthlyTargets)

MonthlyTargets.__table__.create(db.session.bind)