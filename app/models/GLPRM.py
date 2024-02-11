from flask_sqlalchemy import SQLAlchemy

from app.infrastructure.ConnectDB import db

class Glprm(db.Model):
    __tablename__ = 'GLPRM'
    FUND = db.Column(db.String(8), primary_key=True, nullable=False)
    TY_START = db.Column(db.String(8), nullable=False)
    LY_START = db.Column(db.String(40), nullable=False)

    def to_dict(self):
        return {
            'FUND': self.FUND,
            'TY_START':self.TY_START,
            'LY_START': self.LY_START,
            }
