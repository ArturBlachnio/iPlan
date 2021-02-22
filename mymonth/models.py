from mymonth import db
from datetime import timedelta

class Days(db.Model):
    """Daily Activities Records."""
    id = db.Column(db.Date, primary_key=True)
    ds = db.Column(db.Interval)   # Data Science
    dev = db.Column(db.Interval)  # Developer
    pol = db.Column(db.Interval)  # Poliglote
    ge = db.Column(db.Interval)   # Gentleman Explorer
    crt = db.Column(db.Interval)  # Create Read Think
    hs = db.Column(db.Interval)   # Home Son
    alk = db.Column(db.Float)     # Alko

    def __repr__(self):
        return f"Days(id={self.id}, ds={self.ds}, dev={self.dev}, pol={self.pol}, ge={self.ge}, crt={self.crt}, hs={self.hs}, alk={self.alk})"


class Settings(db.Model):
    """General settings for application"""
    id = db.Column(db.Integer, primary_key = True)
    current_month_date = db.Column(db.Date)

    def __repr__(self):
        return f"Settings(id={self.id}, current_month_date={self.current_month_date})"


class MonthlyTargets(db.Model):
    """Target for each month for each category. 
    Id will be set to first date of a month. """
    id = db.Column(db.Date, primary_key=True)
    ds = db.Column(db.Interval, default=timedelta())   # Data Science
    dev = db.Column(db.Interval, default=timedelta())  # Developer
    pol = db.Column(db.Interval, default=timedelta())  # Poliglote
    ge = db.Column(db.Interval, default=timedelta())   # Gentleman Explorer
    crt = db.Column(db.Interval, default=timedelta())  # Create Read Think
    hs = db.Column(db.Interval, default=timedelta())   # Home Son
    alk = db.Column(db.Float, default=0.0)     # Alko
    days0 = db.Column(db.Integer, default=0)     # Alko

    def __repr__(self):
        return f"MonthlyTargets(id={self.id}, ds={self.ds}, dev={self.dev}, pol={self.pol}, ge={self.ge}, crt={self.crt}, hs={self.hs}, alk={self.alk}, days0={self.days0})"
