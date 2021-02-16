from flask import render_template, request, redirect, url_for
from mymonth import db
from mymonth import app
from mymonth.forms import DayEditForm, EditSettings
from mymonth.models import Days, Settings
from mymonth.utils import get_month_days, string_from_duration, duration_from_string, string_from_float, float_from_string, get_target_productive_hours_per_day

from datetime import date, timedelta, datetime
import pandas as pd
import os


def set_initial_values():
    """ Sets initial values. E.g if Settings db is empty - set reference days to today. """
    if Settings.query.first() is None:
        setting1 = Settings(current_month_date=date.today())
        db.session.add(setting1)
        print(f"Initial reference date created and set to {setting1.current_month_date}.")
    db.session.commit()

set_initial_values()


@app.route('/', methods=['GET', 'POST'])
def home():
    REF_DATE = Settings.query.first().current_month_date
    month_start, month_end, month_all_days = get_month_days(REF_DATE)

    # Add a day to database if it does not exist yet. 
    days = Days.query.filter(Days.id >= month_start).filter(Days.id <= month_end).all()
    days_in_db = [day.id for day in days]
    for day_index in month_all_days:
        if day_index not in days_in_db:
            db.session.add(Days(id=day_index))
        db.session.commit()
    
    days = Days.query.filter(Days.id >= month_start).filter(Days.id <= month_end).all()
    
    # Extra fields to display
    cum_TargetHours = timedelta()
    row_with_totals = {'ds': timedelta(), 'dev': timedelta(), 'pol': timedelta(), 'ge': timedelta(), 'crt': timedelta(), 'hs': timedelta()}
    cum_TotalProductive = timedelta()
    cum_TotalNegative = timedelta()
    cum_alk = 0

    for i, day in enumerate(days, start=1):
        # Target Productive Hours
        day.s_TargetHours = get_target_productive_hours_per_day(day.id)

        # Total Productive Time
        day.s_TotalProductive = timedelta(seconds=0)
        for col in row_with_totals:
            value = getattr(day, col)
            if value is not None:
                row_with_totals[col] += value
                day.s_TotalProductive += value

        # Total Negative from Alk
        day.s_TotalNegative = timedelta(seconds=0)
        if day.alk is not None:
            day.s_TotalNegative = max(day.alk - 2.86, 0) * timedelta(minutes=20)
            cum_alk += day.alk

        # % of target
        day.s_PercOfTarget = (day.s_TotalProductive - day.s_TotalNegative) / day.s_TargetHours 

        # Cummulative values 
        cum_TargetHours += day.s_TargetHours
        cum_TotalProductive += day.s_TotalProductive
        cum_TotalNegative += day.s_TotalNegative
        day.cum_PercOfTarget = (cum_TotalProductive - cum_TotalNegative) / cum_TargetHours
        
        day.cum_alk = (cum_alk / i) / 7.8 * 750


        # Styles:
        # Rows with today's date
        day.style_today_tr_hd = ""
        day.style_today_tr_td = ""
        if day.id == date.today():
            day.style_today_tr_hd = "today_header"
            day.style_today_tr_td = "today_cell"
        
    row_with_totals['targethours'] = cum_TargetHours
    row_with_totals['totalproductive'] = cum_TotalProductive

    # Change current month settings
    form_settings = EditSettings()
    settings = Settings.query.first()
    if request.method == 'POST':
        settings.current_month_date = form_settings.current_month_date.data
        db.session.commit()
        return redirect(url_for('home'))

    return render_template('home.html', days=days, f_string_from_duration=string_from_duration, 
                            f_string_from_float=string_from_float, form_settings=form_settings, settings=settings, row_with_totals=row_with_totals)


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


@app.route('/export_to_excel')
def export_db():
    df = pd.read_sql_table('days', db.engine)
    # Change columns type from timedelta/datetime to string
    for col in ['ds', 'dev', 'pol', 'ge', 'crt', 'hs']:
        df[col] = df[col].apply(string_from_duration)
    df.sort_values(by='id').to_excel(os.path.join('mymonth', 'static', 'initial_data', f'export_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx'), index=False, freeze_panes=(1, 0))
    return redirect(url_for('home'))


@app.route('/import_from_excel')
def import_db():
    df = pd.read_excel(os.path.join('mymonth', 'static', 'initial_data', 'import_me.xlsx'))
    # Change columns type from string to timedelta (stored as datetime)
    for col in ['ds', 'dev', 'pol', 'ge', 'crt', 'hs']:
        df[col] = df[col].fillna('').apply(duration_from_string)

    # Overwrite database with new values
    all_current_days = Days.query.all()
    for day in all_current_days:
        db.session.delete(day)
    db.session.commit()

    for index, serie in df.iterrows():
        db.session.add(Days(id=serie['id'], ds=serie['ds'], dev=serie['dev'], pol=serie['pol'], ge=serie['ge'], crt=serie['crt'], hs=serie['hs'], alk=serie['alk']))
    db.session.commit()

    return redirect(url_for('home'))
