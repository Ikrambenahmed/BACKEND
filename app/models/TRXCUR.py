from app.infrastructure.ConnectDB import db


# Define the TRXCUR model
class TRXCUR(db.Model):
    __tablename__ = 'TRXCUR'
    FUND = db.Column(db.String(10), primary_key=True)
    TRADE_DATE = db.Column(db.String(10))
    TRXTYP = db.Column(db.Integer)

    def serialize(self):
        return {
            'FUND': self.FUND,
            'TRADE_DATE': self.TRADE_DATE,
            'TRXTYP': self.TRXTYP
        }
