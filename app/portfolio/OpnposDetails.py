from flask import Blueprint, jsonify
from flask_cors import CORS
from flask import jsonify
from sqlalchemy import text


from app.infrastructure.ConnectDB import db, get_shared_connection

api_getOpnpos_blueprint = Blueprint('api_get_opnpos', __name__)
CORS(api_getOpnpos_blueprint)


@api_getOpnpos_blueprint.route('/getOpnpos/<string:fund>', methods=['GET'])
def api_get_Opnpos(fund):
    try:
        connection = get_shared_connection()

        query = """
            SELECT * FROM OPNPOS WHERE FUND=:fund and (QTY !=0 or LCL_ACCINC!=0) order by tkr 
            """

        # Use SQLAlchemy's text method to bind parameters
        sql_query = text(query)

        # Bind parameters to the query using params method
        result = connection.execute(sql_query.params(fund=fund))

        fund_data = result.fetchall()

        # Get the column names from the result set
        columns = result.keys()

        # Convert the result into a list of dictionaries
        fund_data_list = [dict(zip(columns, row)) for row in fund_data]

        # Close the connection
        connection.close()
        print(f"fund_data_list",fund_data_list)

        return jsonify({'fund_data': fund_data_list})
    except Exception as e:
        # Log the exception stack trace for debugging
        print(f"Error in filter_data_for_fund_and_date_range: {str(e)}")
        return jsonify({'error': str(e)}), 500

