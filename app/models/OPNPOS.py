from flask_sqlalchemy import SQLAlchemy

from app.infrastructure.ConnectDB import db

class Opnpos(db.Model):
    __tablename__ = 'OPNPOS'
    FUND = db.Column(db.String(8), primary_key=True, nullable=False)
    TKR = db.Column(db.String(8), nullable=False)
    QTY = db.Column(db.Float(20,5), nullable=False)
    SECCAT = db.Column(db.String(8), nullable=False)
    TKR_TYPE = db.Column(db.String(1), nullable=False)
    LCLTAXBOOK = db.Column(db.Float(20,4), nullable=False)

    def to_dict(self):
        return {
            'FUND': self.FUND,
            'TKR':self.TKR,
            'QTY': self.QTY,
            'SECCAT': self.SECCAT,
            'TKR_TYPE': self.TKR_TYPE,
            'LCLTAXBOOK': self.LCLTAXBOOK
            # Add other columns as needed
        }
