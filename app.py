import os
from flask import Flask
from flask_cors import CORS

from app.infrastructure.ConnectDB import initialize_db
from app_blueprints import initialize_blueprints

def create_app():
    app = Flask(__name__)
    initialize_blueprints(app)
    CORS(app)
    return app


app_instance = create_app()
initialize_db(app_instance)

if __name__ == '__main__':
    # You can pass the database URI as an argument here
    #app = create_app()
    #app.run(debug=True)

    app_instance.run(debug=True)