from mymonth import db


class Days(db.Model):
    """Daily Activities Records."""
    id = db.Column(db.Date, primary_key = True)
    ds = db.Column(db.Interval)   # Data Science
    dev = db.Column(db.Interval)  # Developer
    pol = db.Column(db.Interval)  # Poliglote
    ge = db.Column(db.Interval)   # Gentleman Explorer
    crt = db.Column(db.Interval)  # Create Read Think
    hs = db.Column(db.Interval)   # Home Son
    alk = db.Column(db.Float)     # Alko

    def __repr__(self):
        return f"Days(id={self.id}, ds={self.ds}, dev={self.dev}, pol={self.pol}, ge={self.ge}, crt={self.crt}, hs={self.hs}, alk={self.alk})"
