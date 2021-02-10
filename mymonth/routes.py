from flask import render_template, request, redirect, url_for
from mymonth import db
from mymonth import app
from mymonth.forms import DayEditForm
from mymonth.models import Days
from mymonth.utils import get_month_days, string_from_duration, duration_from_string, string_from_float, float_from_string, get_target_productive_hours_per_day

from datetime import date, timedelta

 
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
    
    # Extra fields to display
    cum_TargetHours = timedelta()
    cum_TotalProductive = timedelta()
    cum_TotalNegative = timedelta()
    cum_alk = 0
    for i, day in enumerate(days, start=1):
        # Target Productive Hours
        day.s_TargetHours = get_target_productive_hours_per_day(day.id)

        # Total Productive Time
        day.s_TotalProductive = timedelta(seconds=0)
        for col in ['ds', 'dev', 'pol', 'ge', 'crt', 'hs']:
            value = getattr(day, col)
            if value is not None:
                day.s_TotalProductive += value

        # Total Negative from Alk
        day.s_TotalNegative = timedelta(seconds=0)
        if day.alk is not None:
            day.s_TotalNegative = max(day.alk - 2.86, 0)*timedelta(minutes=20)
            cum_alk += day.alk

        # % of target
        day.s_PercOfTarget = (day.s_TotalProductive - day.s_TotalNegative) / day.s_TargetHours 

        # Cummulative values 
        cum_TargetHours += day.s_TargetHours
        cum_TotalProductive += day.s_TotalProductive
        cum_TotalNegative += day.s_TotalNegative
        day.cum_PercOfTarget = (cum_TotalProductive - cum_TotalNegative) / cum_TargetHours
        
        day.cum_alk = (cum_alk / i) / 7.8 * 750

    return render_template('home.html', days=days, f_string_from_duration=string_from_duration, f_string_from_float=string_from_float)


@app.route('/day/edit/<id_day>', methods=['GET', 'POST'])
def edit_day(id_day):
    
    day = Days.query.get_or_404(date.fromisoformat(id_day))
    form_day = DayEditForm()
    
    if request.method == 'POST':
        day.ds = duration_from_string(form_day.ds.data)
        day.dev = duration_from_string(form_day.dev.data)
        day.pol = duration_from_string(form_day.pol.data)
        day.ge = duration_from_string(form_day.ge.data)
        day.crt = duration_from_string(form_day.crt.data)
        day.hs = duration_from_string(form_day.hs.data)
        day.alk = float_from_string(form_day.alk.data)

        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit_day.html', form_day=form_day, day=day, f_string_from_duration=string_from_duration, f_string_from_float=string_from_float)

