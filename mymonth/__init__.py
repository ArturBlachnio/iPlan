from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mymonth.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'c28e87882654f5d1e84b6e1a0c12a77f'

db = SQLAlchemy(app)

# Routes
from mymonth import routes

# Models
from mymonth import models
