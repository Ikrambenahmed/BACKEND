from flask_sqlalchemy import SQLAlchemy

from app.infrastructure.ConnectDB import db

class Fndmas(db.Model):
    __tablename__ = 'FNDMAS'
    FUND = db.Column(db.String(8), primary_key=True, nullable=False)
    BASE_CURR = db.Column(db.String(8), nullable=False)
    ACNAM1 = db.Column(db.String(40), nullable=False)
    DOMICILE = db.Column(db.String(3), nullable=False)
    ACCOUNTANT = db.Column(db.String(8), nullable=False)
    INACTIVE = db.Column(db.String(2), nullable=False)
    def to_dict(self):
        return {
            'FUND': self.FUND,
            'ACNAM1':self.ACNAM1,
            'BASE_CURR': self.BASE_CURR,
            'DOMICILE': self.DOMICILE,
            'ACCOUNTANT': self.ACCOUNTANT,
            'INACTIVE': self.INACTIVE

            # Add other columns as needed
        }
