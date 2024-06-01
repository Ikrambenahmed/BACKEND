from flask_sqlalchemy import SQLAlchemy

from app.infrastructure.ConnectDB import db

class Users(db.Model):
    __tablename__ = 'USERS'
    USER_ID = db.Column(db.String(6),primary_key=True,  nullable=False)
    ADMINPAS = db.Column(db.String(1), nullable=False)
    NAME = db.Column(db.String(25), nullable=True)
    EMAIL = db.Column(db.String(150), nullable=True)

    #ADMIN PAS = Y : inactive , ADMIN PAS= N : active
    def to_dict(self):
        return {
            'USER_ID': self.USER_ID,
            'ADMINPAS':self.ADMINPAS,
            'NAME': self.NAME,
            'EMAIL': self.EMAIL,

        }
    def get_user_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

from datetime import datetime

class TokenBlocklist(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    jti = db.Column(db.String(), nullable=True)
    create_at = db.Column(db.DateTime(), default=datetime.utcnow)

    def __repr__(self):
        return f"<Token {self.jti}>"

    def save(self):
        db.session.add(self)
        db.session.commit()