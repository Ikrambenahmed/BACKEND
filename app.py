import os
from flask import Flask
from flask_cors import CORS

from app.infrastructure.ConnectDB import initialize_db
from app_blueprints import initialize_blueprints

def create_app():
    app = Flask(__name__)
    initialize_db(app)  # Initialize the app with the global SQLAlchemy instance
    initialize_blueprints(app)
    CORS(app)
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
