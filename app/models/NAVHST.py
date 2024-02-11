from flask_sqlalchemy import SQLAlchemy

from app.infrastructure.ConnectDB import db

class Navhst(db.Model):
    __tablename__ = 'NAVHST'

    FUND = db.Column(db.String(8), primary_key=True)
    NET_VALUE = db.Column(db.Float, nullable=False)
    CLASS = db.Column(db.String(20), nullable=False)
    DATED = db.Column(db.Date, nullable=False)
    INCOME = db.Column(db.Float, nullable=False)
    CURNCY = db.Column(db.String(3), nullable=False)
    SUPERVISOR = db.Column(db.String(20), nullable=False)
    TEAM_LEAD = db.Column(db.String(20), nullable=False)
    ACCOUNTANT = db.Column(db.String(20), nullable=False)
    ASSETS = db.Column(db.Float, nullable=False)
    LIABILITY = db.Column(db.Float, nullable=False)
    CAPITAL = db.Column(db.Float, nullable=False)
    REVENUES = db.Column(db.Float, nullable=False)
    EXPENSES = db.Column(db.Float, nullable=False)
    SHARES = db.Column(db.Float, nullable=False)
    FINAL = db.Column(db.String(1), nullable=False)
    STATUS = db.Column(db.Float(4), nullable=False)



    def to_dict(self):
        return {
            'FUND': self.FUND,
            'NET_VALUE': self.NET_VALUE,
            'CLASS': self.CLASS,
            'DATED': self.DATED,
            'INCOME': self.INCOME,
            'CURNCY': self.CURNCY,
            'SUPERVISOR': self.SUPERVISOR,
            'TEAM_LEAD': self.TEAM_LEAD,
            'ACCOUNTANT': self.ACCOUNTANT,
            'ASSETS': self.ASSETS,
            'LIABILITY': self.LIABILITY,
            'CAPITAL': self.CAPITAL,
            'REVENUES': self.REVENUES,
            'EXPENSES': self.EXPENSES,
            'SHARES': self.SHARES,
            'FINAL': self.FINAL,
            'STATUS': self.STATUS

        }
