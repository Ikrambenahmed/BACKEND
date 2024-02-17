from flask_sqlalchemy import SQLAlchemy

from app.infrastructure.ConnectDB import db

class Users(db.Model):
    __tablename__ = 'USERS'
    USER_ID = db.Column(db.String(6),primary_key=True,  nullable=False)
    ADMINPAS = db.Column(db.String(1), nullable=False)
    #ADMIN PAS = Y : inactive , = N : active

    def to_dict(self):
        return {
            'USER_ID': self.USER_ID,
            'ADMINPAS':self.PSWDHASH
        }
