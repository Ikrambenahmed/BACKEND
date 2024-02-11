import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def get_shared_connection():
    print('get_shared_connection')
    return db.session.connection()

def initialize_db(app):
    print('inside initialize_db')
    oracle_client_path = r"C:\instantclient-basic-windows.x64-19.21.0.0.0dbru\instantclient_19_21"
    os.environ["PATH"] = oracle_client_path + ";" + os.environ["PATH"]
    app.config['SQLALCHEMY_DATABASE_URI'] = 'oracle+cx_oracle://UMB_2023_1005:UMB_2023_1005@TN1ODB11.AD.LINEDATA.COM:1521/?service_name=PDBMFT1T.AD.LINEDATA.COM'
    db.init_app(app)
    return db
