from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.fields.html5 import DateField, IntegerField, DecimalField

class DayEditForm(FlaskForm):
    id = DateField(label='Date')
    ds = StringField(label='Data Science')
    dev = StringField(label='Developer')
    pol = StringField(label='Poliglote')
    ge = StringField(label='Gentleman Explorer')
    crt = StringField(label='Create, Think, Read')
    hs = StringField(label='Home, Son')
    alk = StringField(label='SJA')
    submit = SubmitField(label='Save')


class EditSettings(FlaskForm):
    current_month_date = DateField(label="Pick Month")
    submit = SubmitField(label='Save')


class CalculatorSJAForm(FlaskForm):
    ml1 = IntegerField(label="ml", default=0)
    perc1 = DecimalField(label="%", default=13)
    ml2 = IntegerField(label="ml", default=0)
    perc2 = DecimalField(label="%", default=5)
    ml3 = IntegerField(label="ml", default=0)
    perc3 = DecimalField(label="%", default=12)
    submit = SubmitField(label="Calculate SJA")


class EditMonthTargetsForm(FlaskForm):
    id = DateField(label='Month')
    ds = StringField(label='Data Science')
    dev = StringField(label='Developer')
    pol = StringField(label='Poliglote')
    ge = StringField(label='Gentleman Explorer')
    crt = StringField(label='Create, Think, Read')
    hs = StringField(label='Home, Son')
    alk = StringField(label='SJA')
    days0 = StringField(label='Days0')
    submit = SubmitField(label='Save')