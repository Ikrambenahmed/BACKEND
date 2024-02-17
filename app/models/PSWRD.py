from flask_sqlalchemy import SQLAlchemy

from app.infrastructure.ConnectDB import db

class Pswrd(db.Model):
    __tablename__ = 'PSWRD'
    USER_ID = db.Column(db.String(6),  nullable=False)
    PSWDHASH = db.Column(db.String(64),primary_key=True, nullable=False)
    PWRDDATE = db.Column(db.Date, nullable=False)
    PWRDTIME = db.Column(db.String(6), nullable=False)
# Primary Key = USER_ID, PWRDDATE, PWRDTIME
    def to_dict(self):
        return {
            'USER_ID': self.USER_ID,
            'PSWDHASH':self.PSWDHASH,
            'PWRDDATE': self.PWRDDATE,
            'PWRDTIME': self.PWRDTIME,
        }
