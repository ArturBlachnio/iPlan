from flask import render_template
from mymonth import db
from mymonth import app
from mymonth.models import Days
from mymonth.utils import get_month_days
from datetime import date

 
REF_DATE = date(2021, 2, 2)


@app.route('/home')
def main():
    days = Days.query.all()
    return render_template('home.html', days=days)


@app.route('/')
def home():
    month_start, month_end, month_all_days = get_month_days(REF_DATE)

    days = Days.query.filter(Days.id >= month_start).filter(Days.id <= month_end).all()
    # Add a day to database if it does not exist yet. 
    days_in_db = [day.id for day in days]
    for day_index in month_all_days:
        if day_index not in days_in_db:
            db.session.add(Days(id=day_index))
        db.session.commit()
    
    days = Days.query.filter(Days.id >= month_start).filter(Days.id <= month_end).all()
    return render_template('home.html', days=days)