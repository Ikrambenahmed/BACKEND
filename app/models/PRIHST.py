from flask_sqlalchemy import SQLAlchemy

from app.infrastructure.ConnectDB import db

class Prihst(db.Model):
    __tablename__ = 'PRIHST'
    FUND = db.Column(db.String(8),  nullable=False)
    TKR = db.Column(db.String(8),primary_key=True, nullable=False)
    PRCDATE = db.Column(db.Date, nullable=False)
    SOURCE = db.Column(db.String(8), nullable=False)
    PRICE = db.Column(db.Float, nullable=False)


    def to_dict(self):
        return {
            'TKR': self.TKR,
            'FUND':self.FUND,
            'PRCDATE': self.PRCDATE,
            'SOURCE': self.SOURCE,
            'PRICE':self.PRICE
        }
