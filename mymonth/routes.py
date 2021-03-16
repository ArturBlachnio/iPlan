from flask import render_template, request, redirect, url_for
from mymonth import db
from mymonth import app
from mymonth.forms import DayEditForm, EditSettings, CalculatorSJAForm, EditMonthTargetsForm
from mymonth.models import Days, Settings, MonthlyTargets
from mymonth.utils import UtilsDatetime, UtilsDataConversion
from mymonth.utils import (string_from_float,
                           float_from_string, get_target_productive_hours_per_day, get_day_of_month_for_avg_sja,
                           MonthlyGraph)
from mymonth.backup import get_initial_data_from_excel
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import LinearAxis, Range1d, ColumnDataSource, LabelSet

from datetime import date, timedelta, datetime
import pandas as pd
import os
from artools.utils import show_attributes


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
    ref_date = UtilsDatetime(Settings.query.first().current_month_date)

    # Add day(s) to database if it does not exist yet. 
    days = Days.query.filter(Days.id >= ref_date.month_first_date).filter(Days.id <= ref_date.month_last_date).all()
    days_in_db = [day.id for day in days]
    for day_index in ref_date.month_all_dates:
        if day_index not in days_in_db:
            db.session.add(Days(id=day_index))
    db.session.commit()
    
    days = Days.query.filter(Days.id >= ref_date.month_first_date).filter(Days.id <= ref_date.month_last_date).all()
    
    # Extra fields to display in row summary (_s)
    row_with_totals = {'ds': timedelta(), 'dev': timedelta(), 'pol': timedelta(), 'ge': timedelta(), 'crt': timedelta(), 'hs': timedelta()}
    cum_TargetHours = timedelta()
    cum_TargetHours_till_today = timedelta()
    cum_TotalProductive = timedelta()
    cum_TotalNegative = timedelta()
    cum_alk = 0
    cum_days0 = 0 

    for i, day in enumerate(days, start=1):
        # Target Productive Hours depending on weekday
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
            if day.id <= date.today() and day.alk <= 0:
                cum_days0 += 1
        else:
            if day.id <= date.today():
                cum_days0 += 1

        # % of target
        day.s_PercOfTarget = (day.s_TotalProductive - day.s_TotalNegative) / day.s_TargetHours 

        # Cummulative values 
        cum_TargetHours += day.s_TargetHours
        if day.id <= date.today():
            cum_TargetHours_till_today += day.s_TargetHours

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

    day_of_month_for_statistics = get_day_of_month_for_avg_sja(ref_date.month_first_date, ref_date.month_last_date)

    row_with_totals['targethours'] = cum_TargetHours
    row_with_totals['totalproductive'] = cum_TotalProductive
    row_with_totals['totalnegative'] = cum_TotalNegative
    row_with_totals['totalsja'] =  round(cum_alk / day_of_month_for_statistics, 2)
    row_with_totals['totalml'] = int(round(row_with_totals['totalsja'] / 7.8 * 750, 0))
    row_with_totals['totaldays0'] = cum_days0

    # Planned till today
    row_with_totals['targethours_tilltoday'] = cum_TargetHours_till_today

    # Change current month settings
    form_settings = EditSettings()
    settings = Settings.query.first()  # There is only one setting (one date of current month)
    
    # MonthlyTargets
    monthlytargets = MonthlyTargets.query.get(date(year=settings.current_month_date.year, month=settings.current_month_date.month, day=1))
    monthlytargets.ml = int(round(monthlytargets.alk / 7.8 * 750, 0))
    monthlytargets.total_allocated = timedelta(seconds=sum([getattr(monthlytargets, hrscol).total_seconds() for hrscol in ['ds', 'dev', 'pol', 'ge', 'crt', 'hs']]))
    
    row_with_totals['ds_tilltoday'] = monthlytargets.ds * (day_of_month_for_statistics / ref_date.month_last_date.day)
    row_with_totals['dev_tilltoday'] = monthlytargets.dev * (day_of_month_for_statistics / ref_date.month_last_date.day)
    row_with_totals['pol_tilltoday'] = monthlytargets.pol * (day_of_month_for_statistics / ref_date.month_last_date.day)
    row_with_totals['ge_tilltoday'] = monthlytargets.ge * (day_of_month_for_statistics / ref_date.month_last_date.day)
    row_with_totals['crt_tilltoday'] = monthlytargets.crt * (day_of_month_for_statistics / ref_date.month_last_date.day)
    row_with_totals['hs_tilltoday'] = monthlytargets.hs * (day_of_month_for_statistics / ref_date.month_last_date.day)
    row_with_totals['total_tilltoday'] = timedelta(seconds=sum([row_with_totals[f"{hrscol}_tilltoday"].total_seconds() for hrscol in ['ds', 'dev', 'pol', 'ge', 'crt', 'hs']]))

    # Backlog (normal subtraction of timedelta does not work correctly if bigger is subtrackted from smaller object)
    row_with_totals['ds_backlog'] = UtilsDataConversion.string_from_timedelta_subtraction(row_with_totals['ds'], row_with_totals['ds_tilltoday'])
    row_with_totals['dev_backlog'] = UtilsDataConversion.string_from_timedelta_subtraction(row_with_totals['dev'], row_with_totals['dev_tilltoday'])
    row_with_totals['pol_backlog'] = UtilsDataConversion.string_from_timedelta_subtraction(row_with_totals['pol'], row_with_totals['pol_tilltoday'])
    row_with_totals['ge_backlog'] = UtilsDataConversion.string_from_timedelta_subtraction(row_with_totals['ge'], row_with_totals['ge_tilltoday'])
    row_with_totals['crt_backlog'] = UtilsDataConversion.string_from_timedelta_subtraction(row_with_totals['crt'], row_with_totals['crt_tilltoday'])
    row_with_totals['hs_backlog'] = UtilsDataConversion.string_from_timedelta_subtraction(row_with_totals['hs'], row_with_totals['hs_tilltoday'])
    row_with_totals['total_backlog'] = UtilsDataConversion.string_from_timedelta_subtraction(row_with_totals['totalproductive'], row_with_totals['total_tilltoday'])

    # Change displayed month
    if request.method == 'POST':
        settings.current_month_date = form_settings.current_month_date.data
        # Check if monthly targets exist
        targets_date = date(year=settings.current_month_date.year, month=settings.current_month_date.month, day=1)
        if MonthlyTargets.query.get(targets_date) is None:
            db.session.add(MonthlyTargets(id=targets_date))
        db.session.commit()
        return redirect(url_for('home'))

    # Daily graph
    y_alk_cum = [row.cum_alk for row in days]
    y_alk_cum_text = [str(int(row.cum_alk)) for row in days]
    y_score_cum = [row.cum_PercOfTarget for row in days]
    y_score_cum_text = [str(int(round(row.cum_PercOfTarget, 2)*100)) for row in days]
    x_days = [i for i, day in enumerate(ref_date.month_all_dates, start=1)]
    y_todaybar_top = [max(y_alk_cum) if day==date.today() else None for day in ref_date.month_all_dates]

    source = ColumnDataSource(data=dict(x_days=x_days, y_alk_cum=y_alk_cum, y_score_cum=y_score_cum, y_score_cum_text=y_score_cum_text, y_alk_cum_text=y_alk_cum_text, y_todaybar_top=y_todaybar_top))

    plot = figure(title='Daily Progress', x_axis_label='day', y_axis_label='ml cumm.%', plot_width=600, plot_height=400, toolbar_location=None)  

    # Today selection
    plot.vbar(x='x_days', width=1, top='y_todaybar_top', source=source, color='#98FB98', alpha=0.5)

    # Alk
    plot.line(x='x_days', y='y_alk_cum', color="maroon", source=source)
    plot.circle(x='x_days', y='y_alk_cum', color="maroon", fill_color="white", size=5, source=source)
    labels_alk = LabelSet(x='x_days', y='y_alk_cum', text='y_alk_cum_text', text_font_size='10px', text_color='maroon', y_offset=5, level='annotation', source=source, render_mode='canvas')

    # Score
    plot.extra_y_ranges['y_axis_for_target_perc'] = Range1d(min(0, min(source.data.get('y_score_cum'))), max(max(source.data.get('y_score_cum')), 1)*1.05)
    plot.line(x='x_days', y='y_score_cum', source=source, color="cornflowerblue", y_range_name='y_axis_for_target_perc')
    plot.circle(x='x_days', y='y_score_cum', source=source, color="cornflowerblue", fill_color="white", size=5, y_range_name='y_axis_for_target_perc')
    labels_score = LabelSet(x='x_days', y='y_score_cum', text='y_score_cum_text', text_font_size='10px', text_color='cornflowerblue', y_offset=5, y_range_name='y_axis_for_target_perc', level='annotation', source=source, render_mode='canvas')

    ax_right = LinearAxis(y_range_name="y_axis_for_target_perc", axis_label="% of target cum.")
    ax_right.axis_label_text_color ="blue"
    plot.add_layout(ax_right, 'right')
    plot.add_layout(labels_score)
    plot.add_layout(labels_alk)

    bokeh_daily_script, bokeh_daily_div = components(plot)

    # Monthly graph
    month_summary_table = MonthlyGraph(Days).df_months.to_html()
    bokeh_monthly_script, bokeh_monthly_div = MonthlyGraph(Days).bokeh_monthly_components

    return render_template('home.html', days=days, f_string_from_duration=UtilsDataConversion.string_from_timedelta,
                           f_string_from_float=string_from_float, form_settings=form_settings, settings=settings,
                           monthlytargets=monthlytargets, row_with_totals=row_with_totals,
                           bokeh_daily_script=bokeh_daily_script, bokeh_daily_div=bokeh_daily_div, f_round=round,
                           month_summary_table=month_summary_table,
                           bokeh_monthly_script=bokeh_monthly_script, bokeh_monthly_div=bokeh_monthly_div)


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
            return render_template('edit_day.html', form_day=form_day, form_calc_sja=form_calc_sja, sja_values=sja_values, day=day, f_string_from_duration=UtilsDataConversion.string_from_timedelta, f_string_from_float=string_from_float)
        else:
            # print(request.form)
            day.ds = UtilsDataConversion.timedelta_from_string(form_day.ds.data)
            day.dev = UtilsDataConversion.timedelta_from_string(form_day.dev.data)
            day.pol = UtilsDataConversion.timedelta_from_string(form_day.pol.data)
            day.ge = UtilsDataConversion.timedelta_from_string(form_day.ge.data)
            day.crt = UtilsDataConversion.timedelta_from_string(form_day.crt.data)
            day.hs = UtilsDataConversion.timedelta_from_string(form_day.hs.data)
            day.alk = float_from_string(form_day.alk.data)

            db.session.commit()
            return redirect(url_for('home'))
    return render_template('edit_day.html', form_day=form_day, form_calc_sja=form_calc_sja, sja_values=sja_values, day=day, f_string_from_duration=UtilsDataConversion.string_from_timedelta, f_string_from_float=string_from_float)


@app.route('/edit_month_target/<id_month>', methods=['GET', 'POST'])
def edit_month_target(id_month):
    # Get form
    edit_month_targets_form = EditMonthTargetsForm()

    monthly_targets = MonthlyTargets.query.get_or_404(date.fromisoformat(id_month))

    if request.method == 'POST':
        monthly_targets.ds = UtilsDataConversion.timedelta_from_string(edit_month_targets_form.ds.data)
        monthly_targets.dev = UtilsDataConversion.timedelta_from_string(edit_month_targets_form.dev.data)
        monthly_targets.pol = UtilsDataConversion.timedelta_from_string(edit_month_targets_form.pol.data)
        monthly_targets.ge = UtilsDataConversion.timedelta_from_string(edit_month_targets_form.ge.data)
        monthly_targets.crt = UtilsDataConversion.timedelta_from_string(edit_month_targets_form.crt.data)
        monthly_targets.hs = UtilsDataConversion.timedelta_from_string(edit_month_targets_form.hs.data)
        monthly_targets.alk = float_from_string(edit_month_targets_form.alk.data) 
        monthly_targets.days0 = float_from_string(edit_month_targets_form.days0.data) 
        db.session.commit() 
        return redirect(url_for('home')) 

    return render_template('edit_month_targets.html', edit_month_targets_form=edit_month_targets_form,
                           monthly_targets=monthly_targets, f_string_from_duration=UtilsDataConversion.string_from_timedelta, f_string_from_float=string_from_float)


@app.route('/export_to_excel')
def export_db():
    df_days = pd.read_sql_table('days', db.engine)
    df_monthlytargets = pd.read_sql_table('monthly_targets', db.engine)

    # Change columns type from timedelta/datetime to string
    for col in ['ds', 'dev', 'pol', 'ge', 'crt', 'hs']:
        df_days[col] = df_days[col].apply(UtilsDataConversion.string_from_timedelta)
        df_monthlytargets[col] = df_monthlytargets[col].apply(UtilsDataConversion.string_from_timedelta)

    excel_writer = pd.ExcelWriter(os.path.join('mymonth', 'static', 'initial_data', f'export_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx'))
    df_days.sort_values(by='id').to_excel(excel_writer, sheet_name='days', index=False, freeze_panes=(1, 0))
    df_monthlytargets.sort_values(by='id').to_excel(excel_writer, sheet_name='monthly_targets', index=False, freeze_panes=(1, 0))
    excel_writer.save()
    return redirect(url_for('home'))


@app.route('/import_from_excel')
def import_db():
    df_days = get_initial_data_from_excel()
    df_monthlytargets = pd.read_excel(os.path.join('mymonth', 'static', 'initial_data', 'import_me.xlsx'),
                                      sheet_name='monthly_targets')
    # Change columns type from string to timedelta (stored as datetime)
    for col in ['ds', 'dev', 'pol', 'ge', 'crt', 'hs']:
        df_days[col] = df_days[col].fillna('').apply(UtilsDataConversion.timedelta_from_string)
        df_monthlytargets[col] = df_monthlytargets[col].fillna('').apply(UtilsDataConversion.timedelta_from_string)

    # Overwrite database with new values
    all_current_days = Days.query.all()
    for day in all_current_days:
        db.session.delete(day)
    db.session.commit()

    for index, serie in df_days.iterrows():
        db.session.add(Days(id=serie['id'], ds=serie['ds'], dev=serie['dev'], pol=serie['pol'], ge=serie['ge'],
                            crt=serie['crt'], hs=serie['hs'], alk=serie['alk']))
    db.session.commit()

    all_current_targets = MonthlyTargets.query.all()
    for targets in all_current_targets:
        db.session.delete(targets)
    db.session.commit()

    for index, serie in df_monthlytargets.iterrows():
        db.session.add(MonthlyTargets(id=serie['id'], ds=serie['ds'], dev=serie['dev'], pol=serie['pol'],
                                      ge=serie['ge'], crt=serie['crt'], hs=serie['hs'], alk=serie['alk'],
                                      days0=serie['days0']))
    db.session.commit()

    return redirect(url_for('home'))
