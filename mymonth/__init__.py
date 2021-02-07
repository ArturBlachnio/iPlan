from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mymonth.db'

db = SQLAlchemy(app)

# Routes
from mymonth import routes

# Models
from mymonth import models
