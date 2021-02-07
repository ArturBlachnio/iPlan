from flask import render_template
from mymonth import db
from mymonth import app
from mymonth.models import Days
from mymonth.utils import get_month_first_and_last_day, get_all_days_of_month
from datetime import date

 
REF_DATE = date(2021, 3, 2)


@app.route('/home')
def main():
    days = Days.query.all()
    return render_template('home.html', days=days)


@app.route('/')
def home():
    month_start, month_end = get_month_first_and_last_day(REF_DATE)
    all_days_of_month = get_all_days_of_month(REF_DATE)
    days = Days.query.filter(Days.id >= month_start).filter(Days.id <= month_end).all()
    days_in_db = [day.id for day in days]
    # Add a day to database if it does not exist yet. 
    for day_index in all_days_of_month:
        if day_index not in days_in_db:
            db.session.add(Days(id=day_index))
        db.session.commit()
    
    days = Days.query.filter(Days.id >= month_start).filter(Days.id <= month_end).all()
    return render_template('home.html', days=days)