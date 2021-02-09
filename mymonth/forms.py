from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.fields.html5 import DateField

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
