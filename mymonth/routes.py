from flask import render_template, request, redirect, url_for
from mymonth import db
from mymonth import app
from mymonth.forms import DayEditForm, EditSettings, CalculatorSJAForm, EditMonthTargetsForm
from mymonth.models import Days, Settings, MonthlyTargets
from mymonth.utils import get_month_days, string_from_duration, duration_from_string, string_from_float, float_from_string, get_target_productive_hours_per_day

from datetime import date, timedelta, datetime
import pandas as pd
import os
from artools.utils import show_attributes

# show_attributes(MonthlyTargets.__tablename__)
print(MonthlyTargets.__tablename__)


def set_initial_db():
    """Temporary solution for development. Checks if db exists. If not, creates it. Also sets initial values for current_month_date. 
    E.g.: if Settings is empty - set reference day to today."""

    if not os.path.exists('mymonth/mymonth.db'):
        print(f"Database does not exist. Create in")
        db.create_all()

    if Settings.query.first() is None:
        db.session.add(Settings(current_month_date=date.today()))
        db.session.commit()

    if MonthlyTargets.query.first() is None:
        id_month = date(year=date.today().year, month=date.today().month, day=1)
        current_month_target = MonthlyTargets(id=id_month)
        db.session.add(current_month_target)
        db.session.commit()

set_initial_db()


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
    
    # MonthlyTargets
    monthlytargets = MonthlyTargets.query.get(date(year=settings.current_month_date.year, month=settings.current_month_date.month, day=1))
    monthlytargets.ml = int(round(monthlytargets.alk / 7.8 * 750, 0))
    monthlytargets.total_allocated = timedelta(seconds=sum([getattr(monthlytargets, hrscol).total_seconds() for hrscol in ['ds', 'dev', 'pol', 'ge', 'crt', 'hs']]))
  
    if request.method == 'POST':
        settings.current_month_date = form_settings.current_month_date.data
        # Check if monthly targets exist
        targets_date = date(year=settings.current_month_date.year, month=settings.current_month_date.month, day=1)
        if MonthlyTargets.query.get(targets_date) is None:
            db.session.add(MonthlyTargets(id=targets_date))
        db.session.commit()
        return redirect(url_for('home'))

    return render_template('home.html', days=days, f_string_from_duration=string_from_duration, f_string_from_float=string_from_float, 
                            form_settings=form_settings, settings=settings, monthlytargets=monthlytargets, row_with_totals=row_with_totals)


@app.route('/day/edit/<id_day>', methods=['GET', 'POST'])
def edit_day(id_day):
    
    day = Days.query.get_or_404(date.fromisoformat(id_day))
    form_day = DayEditForm()
    form_calc_sja = CalculatorSJAForm()
    sja_values = dict(zip(['sja1', 'sja2', 'sja3'], [0, 0, 0]))

    if request.method == 'POST':
        if request.form.get("submit") == 'Calculate SJA':
            print("Just calcualted SJA")
            sja1 = float(form_calc_sja.ml1.data * (form_calc_sja.perc1.data / 100)) / 12.5
            sja2 = float(form_calc_sja.ml2.data * (form_calc_sja.perc2.data / 100)) / 12.5
            sja3 = float(form_calc_sja.ml3.data * (form_calc_sja.perc3.data / 100)) / 12.5
            day.alk = round(sum([sja1, sja2, sja3]), 1)
            sja_values = dict(zip(['sja1', 'sja2', 'sja3'], [round(sja1, 2), round(sja2, 2), round(sja3, 2)]))
            return render_template('edit_day.html', form_day=form_day, form_calc_sja=form_calc_sja, sja_values=sja_values, day=day, f_string_from_duration=string_from_duration, f_string_from_float=string_from_float)
        else:
            # print(request.form)
            day.ds = duration_from_string(form_day.ds.data)
            day.dev = duration_from_string(form_day.dev.data)
            day.pol = duration_from_string(form_day.pol.data)
            day.ge = duration_from_string(form_day.ge.data)
            day.crt = duration_from_string(form_day.crt.data)
            day.hs = duration_from_string(form_day.hs.data)
            day.alk = float_from_string(form_day.alk.data)

            db.session.commit()
            return redirect(url_for('home'))
    return render_template('edit_day.html', form_day=form_day, form_calc_sja=form_calc_sja, sja_values=sja_values, day=day, f_string_from_duration=string_from_duration, f_string_from_float=string_from_float)


@app.route('/edit_month_target/<id_month>', methods=['GET', 'POST'])
def edit_month_target(id_month):
    # Get form
    edit_month_targets_form = EditMonthTargetsForm()

    monthly_targets = MonthlyTargets.query.get_or_404(date.fromisoformat(id_month))

    if request.method == 'POST':
        monthly_targets.ds = duration_from_string(edit_month_targets_form.ds.data)  
        monthly_targets.dev = duration_from_string(edit_month_targets_form.dev.data) 
        monthly_targets.pol = duration_from_string(edit_month_targets_form.pol.data) 
        monthly_targets.ge = duration_from_string(edit_month_targets_form.ge.data) 
        monthly_targets.crt = duration_from_string(edit_month_targets_form.crt.data) 
        monthly_targets.hs = duration_from_string(edit_month_targets_form.hs.data) 
        monthly_targets.alk = float_from_string(edit_month_targets_form.alk.data) 
        db.session.commit() 
        return redirect(url_for('home')) 

    return render_template('edit_month_targets.html', edit_month_targets_form=edit_month_targets_form, 
                            monthly_targets=monthly_targets, f_string_from_duration=string_from_duration, f_string_from_float=string_from_float)


@app.route('/export_to_excel')
def export_db():
    df_days = pd.read_sql_table('days', db.engine)
    df_monthlytargets = pd.read_sql_table('monthly_targets', db.engine)

    # Change columns type from timedelta/datetime to string
    for col in ['ds', 'dev', 'pol', 'ge', 'crt', 'hs']:
        df_days[col] = df_days[col].apply(string_from_duration)
        df_monthlytargets[col] = df_monthlytargets[col].apply(string_from_duration)

    excel_writer = pd.ExcelWriter(os.path.join('mymonth', 'static', 'initial_data', f'export_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx'))
    df_days.sort_values(by='id').to_excel(excel_writer, sheet_name='days', index=False, freeze_panes=(1, 0))
    df_monthlytargets.sort_values(by='id').to_excel(excel_writer, sheet_name='monthly_targets', index=False, freeze_panes=(1, 0))
    excel_writer.save()
    return redirect(url_for('home'))


@app.route('/import_from_excel')
def import_db():
    df_days = pd.read_excel(os.path.join('mymonth', 'static', 'initial_data', 'import_me.xlsx'), sheet_name='days')
    df_monthlytargets = pd.read_excel(os.path.join('mymonth', 'static', 'initial_data', 'import_me.xlsx'), sheet_name='monthly_targets')
    # Change columns type from string to timedelta (stored as datetime)
    for col in ['ds', 'dev', 'pol', 'ge', 'crt', 'hs']:
        df_days[col] = df_days[col].fillna('').apply(duration_from_string)
        df_monthlytargets[col] = df_monthlytargets[col].fillna('').apply(duration_from_string)

    # Overwrite database with new values
    all_current_days = Days.query.all()
    for day in all_current_days:
        db.session.delete(day)
    db.session.commit()

    for index, serie in df_days.iterrows():
        db.session.add(Days(id=serie['id'], ds=serie['ds'], dev=serie['dev'], pol=serie['pol'], ge=serie['ge'], crt=serie['crt'], hs=serie['hs'], alk=serie['alk']))
    db.session.commit()

    all_current_targets = MonthlyTargets.query.all()
    for targets in all_current_targets:
        db.session.delete(targets)
    db.session.commit()

    for index, serie in df_monthlytargets.iterrows():
        db.session.add(MonthlyTargets(id=serie['id'], ds=serie['ds'], dev=serie['dev'], pol=serie['pol'], ge=serie['ge'], crt=serie['crt'], hs=serie['hs'], alk=serie['alk']))
    db.session.commit()

    return redirect(url_for('home'))
