
from app.infrastructure.ConnectDB import db

class Usrfnd(db.Model):
    __tablename__ = 'USRFND'
    FUND = db.Column(db.String(8), primary_key=True, nullable=False)
    USER_ID = db.Column(db.String(6),primary_key=True,  nullable=False)
    def to_dict(self):
        return {
            'FUND': self.FUND,
            'USER_ID':self.USER_ID,
        }
