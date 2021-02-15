from mymonth import db
from mymonth.models import Days, Settings

# db.create_all()

Settings.query.first() is None:
    