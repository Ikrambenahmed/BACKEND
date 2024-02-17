import os
import json
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


db = SQLAlchemy()
db_session = None
def init_dbOLD():
    db_config = get_db_config()
    engine = create_engine(db_config['db_uri'])
    db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
    return db_session

def get_db_config():
    with open('database_uri.json', 'r') as json_file:
        db_config = json.load(json_file)
    return db_config

def set_db_config(db_uri):
    with open('database_uri.json', 'w') as json_file:
        json.dump({'db_uri': db_uri}, json_file)

def initialize_db(app, db_uri=None):
    if db_uri is None:
      db_uri = get_db_config()['db_uri']
    else:
        # If db_uri is provided during the session, update the file with the new value
      set_db_config(db_uri)

    oracle_client_path = r"C:\instantclient-basic-windows.x64-19.21.0.0.0dbru\instantclient_19_21"
    os.environ["PATH"] = oracle_client_path + ";" + os.environ["PATH"]

    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    db.init_app(app)


def get_db_session():
    global db_session
    return db_session

def get_shared_connection():
    print('get_shared_connection')
    return db.session.connection()
def init_db(app, db_uri):
    global db_session
    oracle_client_path = r"C:\instantclient-basic-windows.x64-19.21.0.0.0dbru\instantclient_19_21"
    os.environ["PATH"] = oracle_client_path + ";" + os.environ["PATH"]

    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    db.init_app(app)
    db_session = db.session  # You can use db_session as your database session

def get_db_session():
    global db_session
    return db_session

def initialize_dbold(app, db_uri=None):
    print('inside initialize_db')

    if db_uri is None:
        # Load the database URI from the file or database
        with open('database_uri.json', 'r') as f:
            data = json.load(f)
            db_uri = data['db_uri']

    oracle_client_path = r"C:\instantclient-basic-windows.x64-19.21.0.0.0dbru\instantclient_19_21"
    os.environ["PATH"] = oracle_client_path + ";" + os.environ["PATH"]
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    db.init_app(app)
    return db
