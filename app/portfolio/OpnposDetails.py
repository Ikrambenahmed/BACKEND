from flask import Blueprint, jsonify
from flask_cors import CORS
from flask import jsonify
from sqlalchemy import text, func, desc, and_
from tensorflow.python.ops.gen_math_ops import Round

from app.infrastructure.ConnectDB import db, get_shared_connection, db_session
from app.models.NAVHST import Navhst
from app.models.OPNPOS import Opnpos

api_getOpnpos_blueprint = Blueprint('api_get_opnpos', __name__)
api_getTotals_blueprint= Blueprint('api_getTotals', __name__)
api_AssetAllocation_blueprint= Blueprint('api_AssetAllocation', __name__)
CORS(api_AssetAllocation_blueprint)
CORS(api_getOpnpos_blueprint)
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
        print(f"open pos tickers",fund_data_list)

        return jsonify({'fund_data': fund_data_list})
    except Exception as e:
        # Log the exception stack trace for debugging
        print(f"Error in filter_data_for_fund_and_date_range: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_getTotals_blueprint.route('/calculate_totals', methods=['GET'])
def calculate_totals():
    try:
        # Subquery to get the latest date for each fund
        latest_fund_subquery = (
            db.session.query(
                Navhst.FUND,
                func.max(Navhst.DATED).label('latest_date'),
            )
            .group_by(Navhst.FUND)
            .subquery('latest_fund_subquery')
        )
        print('latest_fund_subquery',latest_fund_subquery);

        # Use SQLAlchemy to query the latest records for each fund
        latest_records = (
            db.session.query(
                Navhst.FUND,
                Navhst.DATED.label('latest_date'),
                Navhst.ASSETS.label('latest_assets'),
                Navhst.NET_VALUE.label('latest_nav'),
                Navhst.LIABILITY.label('latest_liabilities'),
            )
            .join(
                latest_fund_subquery,
                and_(
                    Navhst.FUND == latest_fund_subquery.c.FUND,
                    Navhst.DATED == latest_fund_subquery.c.latest_date,
                )
            )
            .all()
        )
        print('latest_records',latest_records)
        # Calculate total values
        total_assets = round(sum(record.latest_assets for record in latest_records), 2)
        total_nav = round(sum(record.latest_nav for record in latest_records), 2)
        total_liabilities = round(sum(record.latest_liabilities for record in latest_records), 2)

        # Create and return the JSON response
        json_result = {
            'total_assets': total_assets,
            'total_nav': total_nav,
            'total_liabilities': total_liabilities,
        }
        return jsonify(json_result)

    except Exception as e:
        # Log the exception stack trace for debugging
        print(f"Error in calculate_totals API: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_AssetAllocation_blueprint.route('/AssetAllocation', methods=['GET'])
def calculate_AssetAllocation():
    try:
        # Query to get the most traded ticker types
        most_traded_ticker_types = (
            db.session.query(Opnpos.TKR_TYPE, func.count().label('opnpos_count'))
            .group_by(Opnpos.TKR_TYPE)
            .order_by(func.count().desc())
            .limit(4)
            .all()
        )

        # Query to get the total count of all ticker types
        total_count = db.session.query(func.count()).select_from(Opnpos).scalar()

        result = {
            'most_traded_ticker_types': [
                {
                    'tkr_type': tkr_type,
                    'opnpos_count': trade_count,
                    'label': get_tkr_type_label(tkr_type),
                    'progressPercentage': round((trade_count / total_count) * 100, 2)  # Round to 2 decimal places
                }
                for tkr_type, trade_count in most_traded_ticker_types
            ]
        }

        return jsonify(result)

    except Exception as e:
        # Log the exception stack trace for debugging
        print(f"Error in calculate_AssetAllocation API: {str(e)}")
        return jsonify({'error': str(e)}), 500

def get_tkr_type_label(tkr_type):
    # Define a mapping of tkr_type to labels
    label_mapping = {
        '1': 'Equity',
        '2': 'CFD',
        '3': 'Bond',
        '4':'Forwards',
        # Add more mappings as needed
    }

    # Return the corresponding label or 'Other' if not found
    return label_mapping.get(tkr_type, 'Other')

