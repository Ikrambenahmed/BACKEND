import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from app.infrastructure.ConnectDB import initialize_db, db
from app.models.USERS import Users, TokenBlocklist
from app_blueprints import initialize_blueprints

def create_app():
    app = Flask(__name__)
    app.config['JWT_SECRET_KEY'] = 'ikram123'
    jwt = JWTManager(app)

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



    