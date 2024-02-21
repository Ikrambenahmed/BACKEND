import hashlib
import cx_Oracle
import sqlalchemy
from flask_cors import CORS, cross_origin
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.exc import OperationalError

from app.infrastructure.ConnectDB import init_db, set_db_config, initialize_db
from app.models.PSWRD import Pswrd
from flask import Blueprint, current_app
from flask import jsonify, request
from sqlalchemy import func, create_engine
from sqlalchemy import text

from app.models.USERS import Users
import cx_Oracle
global_db = None

api_Login_blueprint = Blueprint('api_Login', __name__)
CORS(api_Login_blueprint)

api_SetDatabase_blueprint=Blueprint('api_SetDatabase', __name__)
api_TestConnection_blueprint = Blueprint("api_TestConnection", __name__)
api_Logout_blueprint= Blueprint("api_Logout", __name__)
api_ConnectToDB_blueprint= Blueprint("api_ConnectToDB", __name__)

CORS(api_ConnectToDB_blueprint)
CORS(api_TestConnection_blueprint)
CORS(api_Logout_blueprint)
CORS(api_SetDatabase_blueprint)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest().upper()


@api_Login_blueprint.route('/login', methods=['POST'])
def login1():
    try:
        # Get JSON data from the request
        request_data = request.get_json()

        # Extract parameters from JSON data
        USER_ID = request_data.get('USER_ID')
        password = request_data.get('pswrd')

        # Hash the password
        PSWDHASH = hash_password(password)

        # Check if the user exists in the USERS table with ADMINPAS=N
        user = Users.query.filter_by(USER_ID=USER_ID).first()

        print(f"USER_ID: {USER_ID}, PSWDHASH: {PSWDHASH}")
        print(f'user from db: {user}')

        if user:
            retrieved_user_id = user.USER_ID

            # If the user exists, check the PSWRD table for the hashed password
            pswrd = Pswrd.query.filter_by(USER_ID=retrieved_user_id, PSWDHASH=PSWDHASH).first()

            if pswrd:
                # Use create_access_token to generate a JWT token
                access_token = create_access_token(identity=USER_ID)

                # Return the response with the access_token
                return {'access_token': access_token, 'login_response': {'login': True, 'message': 'Login successful!'}}
            else:
                return {'login_response': {'login': False, 'message': 'Incorrect password!'}}

        return {'login_response': {'login': False, 'message': 'User not found or not authorized!'}}

    except Exception as e:
        # Log the exception stack trace for debugging
        print(f"Error in login: {str(e)}")
        return {'error': str(e)}, 500

@api_TestConnection_blueprint.route("/test_connection", methods=["POST"])
def test_connection():
    try:
        data = request.get_json()

        if not all(key in data for key in ["username", "password", "host", "port", "service_name"]):
            return jsonify({"error": "Incomplete database information provided"}), 400

        # Construct the database URI
        db_uri = f"oracle+cx_oracle://{data['username']}:{data['password']}@{data['host']}:{data['port']}/?service_name={data['service_name']}"
        print('db_uri',db_uri)
        # Test the database connection
        engine = create_engine(db_uri)
        connection = engine.connect()
        connection.close()

        return jsonify({"message": "Database connection successful", "success": True}), 200

    except SQLAlchemyError as e:
        # Log the exception stack trace for debugging
        print(f"Error in test_connection: {str(e)}")
        return jsonify({"message": f"Database connection failed: {str(e)}", "success": False}), 500

global db_session


@api_SetDatabase_blueprint.route('/set_database', methods=['POST'])
def set_database_connection():
    global db_session
    data = request.get_json()
    print('data', data)

    required_fields = ['username', 'password', 'host', 'port', 'service_name', 'USER_ID']
    if any(field not in data for field in required_fields):
        return jsonify({'error': 'Incomplete information provided'}), 400

    try:
        # Construct the database URI
        db_uri = f"oracle+cx_oracle://{data['username']}:{data['password']}@{data['host']}:{data['port']}/?service_name={data['service_name']}"
        print('db_uri', db_uri)
        with current_app.app_context():

            db_uri = f"oracle+cx_oracle://{data['username']}:{data['password']}@{data['host']}:{data['port']}/?service_name={data['service_name']}"
            print('db_uri', db_uri)
            # Test the database connection
            engine = create_engine(db_uri)
            connection = engine.connect()
            print("after engine.connect")

            # Your code that uses global_db_connection

        print('global_db_connection',connection)
        # Check if the connection is successful before proceeding with login
        if connection:
            set_db_config(db_uri)
            current_app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
            current_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
            print("Inside connection if")
            # Initialize the SQLAlchemy extension with the updated configuration


            login_response = login(connection, data['USER_ID'], data['pswrd'])
            # Get the current Flask app instance
            access_token = create_access_token(identity=data['USER_ID'])

            # Modify the response based on the login result
            return jsonify({'login_response': login_response, 'access_token': access_token}), 200
        else:
            return jsonify({'error': 'Failed to connect to the database'}), 500

    except KeyError as e:
        return jsonify({'error': f'Missing key in JSON data: {e}'}), 400

    except OperationalError as e:
        # Log the exception stack trace for debugging
        print(f"Error connecting to the database: {str(e)}")
        return jsonify({'error': 'Failed to connect to the database'}), 500

    except Exception as e:
        # Log the exception stack trace for debugging
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


def login(connection, USER_ID, password):
    try:
        print('connection',connection)
        print ('database_name', sqlalchemy.engine.base.Connection)

        # Hash the password
        PSWDHASH = hash_password(password)

        # Check if the user exists in the USERS table with ADMINPAS=N
        user_query = text("SELECT * FROM Users WHERE USER_ID = :user_id")
        user_result  = connection.execute(user_query, {'user_id': USER_ID}).fetchone()

        print(f"USER_ID: {USER_ID}, PSWDHASH: {PSWDHASH}")
        print(f'user from db: {user_result}')

        if user_result:
            retrieved_user_id = user_result[0]  # Index 0 corresponds to the USER_ID column

            # If the user exists, check the PSWRD table for the hashed password
            pswrd_query = text("SELECT * FROM Pswrd WHERE USER_ID = :user_id AND PSWDHASH = :pswdhash")
            pswrd = connection.execute(pswrd_query, {'user_id': retrieved_user_id, 'pswdhash': PSWDHASH}).fetchone()
            print('pswrd from db', pswrd)
            if pswrd:

                return {'login': True, 'message': 'Login successful!'}
            else:
                return {'login': False, 'message': 'Incorrect password!'}

        return {'login': False, 'message': 'User not found or not authorized!'}

    except Exception as e:
        # Log the exception stack trace for debugging
        print(f"Error in login: {str(e)}")
        return {'error': str(e)}

from flask import current_app, jsonify

def close_database_connection(db_session):
    with current_app.app_context():
        if db_session is not None:
            db_session.remove()
            print("Database connection closed")
        else:
            print("No active database connection to close")


@api_ConnectToDB_blueprint.route('/ConnectDB', methods=['POST'])
def connect_database():
    global db_session
    data = request.get_json()

    required_fields = ['username', 'password', 'host', 'port', 'service_name']
    if any(field not in data for field in required_fields):
        return jsonify({'error': 'Incomplete information provided'}), 400

    try:
        # Construct the database URI
        db_uri = f"oracle+cx_oracle://{data['username']}:{data['password']}@{data['host']}:{data['port']}/?service_name={data['service_name']}"
        print('db_uri', db_uri)

        with current_app.app_context():
            try:
                # Initialize the app with the provided db_uri
                initialize_db(current_app, db_uri)

                # Other database connection logic goes here...

                return jsonify({'message': 'Connected to the database successfully'}), 200
            except KeyError as e:
                return jsonify({'error': f'error connection: {e}'}), 400

    except KeyError as e:
        return jsonify({'error': f'Missing key in JSON data: {e}'}), 400

    except Exception as e:
        # Log the exception stack trace for debugging
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Example protected route with JWT authentication
@api_SetDatabase_blueprint.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    # Access the current user's identity using get_jwt_identity()
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200
