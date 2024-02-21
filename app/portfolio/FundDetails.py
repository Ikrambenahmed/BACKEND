from flask import Blueprint, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import jwt_required
from sqlalchemy import desc, asc
from app.infrastructure.ConnectDB import db, get_shared_connection
from app.models import PRIHST
from app.models.FNDMAS import Fndmas
from app.models.PRIHST import Prihst
from sqlalchemy import text

from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt,
    current_user,
    get_jwt_identity,
)

from app.models.GLPRM import Glprm
from app.infrastructure.ConnectDB import db
from app.models.NAVHST import Navhst
import logging

from app.models.USRFND import Usrfnd

api_getFndmas_blueprint = Blueprint('api_get_fndmas', __name__)
api_getNAVHSTFndmas_blueprint = Blueprint('api_get_Navhstfndmas', __name__)
api_getALLFndmas_blueprint= Blueprint('api_getALLFndmas', __name__)
api_getALLPrices_blueprint = Blueprint('api_getALLPrices', __name__)
api_getCashMovement_blueprint = Blueprint('api_getCashMovement', __name__)
api_getQtyMovement_blueprint= Blueprint('api_getQtyMovement', __name__)
api_getUsrFnd_blueprint= Blueprint('api_getUsrFnd', __name__)

CORS(api_getUsrFnd_blueprint)
CORS(api_getQtyMovement_blueprint)
CORS(api_getALLFndmas_blueprint)
CORS(api_getFndmas_blueprint)
CORS(api_getNAVHSTFndmas_blueprint)
CORS(api_getALLPrices_blueprint)
CORS(api_getCashMovement_blueprint)

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

def result_to_dict(result):
    return dict(result)

@api_getFndmas_blueprint.route('/getFndmas/<string:fund>', methods=['GET'])
def api_get_fndmas(fund):
    # Query Fndmas records
    fndmas_records = Fndmas.query.filter_by(FUND=fund).first()
    fndmas_list = fndmas_records.to_dict() if fndmas_records else None

    # Query the latest Navhst record with Final Nav = Y and STATUS=1
    latest_navhst_record = (
        Navhst.query
        .filter_by(FUND=fund, STATUS=1)
        .order_by(desc(Navhst.DATED))  # Assuming you have a column representing the date
        .first()
    )
    print('Latest Navhst DATED:', latest_navhst_record.DATED)
    date1 = latest_navhst_record.DATED
    print('date1 date1 date1:', date1)
    formatted_date1 = date1.strftime("%m/%d/%Y")

    query = """
        SELECT * FROM NAVHST 
        WHERE FUND = :fund AND STATUS = 1 AND DATED < TO_DATE(:formatted_date1, 'MM/DD/YYYY')
        ORDER BY DATED DESC
    """

    # Execute the query
    connection = get_shared_connection()
    result = connection.execute(text(query).params(fund=fund, formatted_date1=formatted_date1))
    previous_navhst_record = result.fetchall()
    columns = result.keys()

    # Convert the result into a list of dictionaries
        # Convert the result into a list of dictionaries
    previous_navhst_list = [dict(zip(columns, row)) for row in previous_navhst_record]
    # Extract only the first record from the list
    first_previous_navhst_dict = previous_navhst_list[0] if previous_navhst_list else None

    print('first_previous_navhst_dict',first_previous_navhst_dict)

    latest_navhst_dict = latest_navhst_record.to_dict() if latest_navhst_record else None

    # Calculate percentage change based on NET_VALUE
    percentage_change = None

    if latest_navhst_dict and first_previous_navhst_dict:
        latest_net_value = float(latest_navhst_dict.get('NET_VALUE', 0))
        first_previous_net_value =float( first_previous_navhst_dict.get('net_value', 0))
        print('latest_net_value',latest_net_value)
        print('first_previous_net_value',first_previous_net_value)

        if first_previous_net_value != 0:
            percentage_change = ((latest_net_value - first_previous_net_value) / first_previous_net_value) * 100
    rounded_percentage_change = round(percentage_change, 2) if percentage_change is not None else None

    if latest_navhst_dict and first_previous_navhst_dict:
        latest_assets = float(latest_navhst_dict.get('ASSETS', 0))
        first_previous_assets = float(first_previous_navhst_dict.get('assets', 0))
        latest_liabilities = float(latest_navhst_dict.get('LIABILITY', 0))
        first_previous_liabilities = float(first_previous_navhst_dict.get('liability', 0))

        # Calculate percentage change for assets
        if first_previous_assets != 0:
            assets_percentage_change = ((latest_assets - first_previous_assets) / first_previous_assets) * 100
        else:
            assets_percentage_change = None

        # Calculate percentage change for liabilities
        if first_previous_liabilities != 0:
            liabilities_percentage_change = ((
                                                         latest_liabilities - first_previous_liabilities) / first_previous_liabilities) * 100
        else:
            liabilities_percentage_change = None

        # Round the percentage changes
        rounded_assets_percentage_change = round(assets_percentage_change,
                                                 2) if assets_percentage_change is not None else None
        rounded_liabilities_percentage_change = round(liabilities_percentage_change,
                                                      2) if liabilities_percentage_change is not None else None

        print('Assets Percentage Change:', rounded_assets_percentage_change)
        print('Liabilities Percentage Change:', rounded_liabilities_percentage_change)

    print('Percentage Change:', percentage_change)
    # Query GLPRM records
    glprm_records = Glprm.query.filter_by(FUND=fund).first()
    glprm_dict = glprm_records.to_dict() if glprm_records else None

    # Combine Fndmas, latest Navhst, and previous Navhst records into a single dictionary
    combined_data = {'FNDMAS': fndmas_list, 'LatestNAVHST': latest_navhst_dict, 'PreviousNavhst': first_previous_navhst_dict,'percentage_change':rounded_percentage_change,
                     'assets_percentage_change':rounded_assets_percentage_change,'liabilities_percentage_change':rounded_liabilities_percentage_change, 'GLPRM': glprm_dict}
    json_result = {'data': combined_data}
    return jsonify(json_result)

@api_getALLFndmas_blueprint.route('/getAllFunds', methods=['GET'])
def api_getAll_fndmas():

    try:
            fndmas_records = Fndmas.query.filter_by(INACTIVE='N').order_by(asc(Fndmas.FUND)).all()
            print("All fndmas_records")
            fndmas_list = [record.to_dict() for record in fndmas_records]
            json_result = {'data': fndmas_list}
            return jsonify(json_result)

    except Exception as e:
        # Log the exception stack trace for debugging
        print(f"Error in another_api: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_getNAVHSTFndmas_blueprint.route('/getNAVHSTFndmas/<string:fund>', methods=['GET'])
def api_get_NAVHSTfndmas(fund):
    navhst_records = Navhst.query.filter_by(FUND=fund).all()

    print('navhst records',navhst_records)
    navhst_list = [record.to_dict() for record in navhst_records]
    print('navhst_list',navhst_list)
    json_result = {'data': navhst_list}
    return jsonify(json_result)

@api_getALLPrices_blueprint.route('/getAllPrices/<string:fund>/<string:tkr>', methods=['GET'])
def api_getAll_Prices(tkr,fund):
    try:
        connection = get_shared_connection()
        query = """
        SELECT
          fund,
          prcdate,
          price, source, tkr
 FROM PRIHST where fund=:fund and tkr=:tkr """
        sql_query = text(query)
        result = connection.execute(sql_query.params(fund=fund, tkr=tkr))
        fund_data = result.fetchall()
        # Get the column names from the result set
        columns = result.keys()
        # Convert the result into a list of dictionaries
        prices_data_list = [dict(zip(columns, row)) for row in fund_data]
        # Close the connection
        connection.close()
        return jsonify({'data': prices_data_list})
    except Exception as e:
        # Log the exception stack trace for debugging
        print(f"Error in filter_data_for_fund_and_date_range: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_getQtyMovement_blueprint.route('/getQty/<string:fund>/<string:tkr>', methods=['GET'])
def getQtyMovement_blueprint(tkr,fund):
    try:
        connection = get_shared_connection()
        query = """
     SELECT 
    FUND, 
    TKR, 
    TAXLOT_ID,
    TRADE_DATE,
    QTY
FROM (
    SELECT 
        TC.FUND, 
        TC.TKR, 
        TC.TAXLOT_ID,
        TC.TRADE_DATE,
        - NVL(
            SUM(
                CASE 
                    WHEN (
                        ((T.BUY_SELL = 'S') AND ((TC.LONG_SHORT = 'S') AND T.TRXTYP NOT IN ('1360', '1255', '1485', '1245', '1330', '1129', '1123', '1126', '1122')))
                        OR
                        (
                            (T.BUY_SELL = 'B')
                            AND
                            (
                                (TC.LONG_SHORT = 'L') OR (T.TRXTYP = '1190')
                                OR
                                (
                                    (TC.LONG_SHORT IS NULL) OR ((TC.LONG_SHORT IS NOT NULL) AND (T.TRXTYP IN ('1480', '1490')))
                                )
                            )
                        )
                    )
                    OR
                    (
                        (T.BUY_SELL IS NULL)
                        AND
                        (
                            (T.TRXTYP <> '1128') AND (T.TRXTYP <> '1440') AND 
                            (
                                (T.TRXTYP = '1445') 
                                OR 
                                (
                                    (T.TRXTYP <> '1455') 
                                    AND 
                                    (
                                        ((T.QTY <> 'N') AND (TC.LONG_SHORT = 'L')) 
                                        OR 
                                        ((TC.LONG_SHORT <> 'L') AND (T.TRXTYP IN ('1170', '1175')))
                                    )
                                )
                            )
                        )
                    )
                THEN
                    CASE 
                        WHEN (TC.REVFLG = 'N' OR TC.REVFLG IS NULL)
                        THEN
                            -TC.QTY
                        ELSE
                            +TC.QTY
                    END
                END
            ), 0
        )
        +
        NVL(
            SUM(
                CASE 
                    WHEN (
                        ((T.BUY_SELL = 'S') AND (TC.LONG_SHORT = 'L'))
                        OR
                        (T.BUY_SELL = 'S') AND (((TC.LONG_SHORT = 'L') OR ((TC.LONG_SHORT = 'S') AND T.TRXTYP IN ('1360', '1255', '1485', '1245', '1330', '1129', '1123', '1126', '1122'))))
                        OR
                        ((T.BUY_SELL = 'B') AND (TC.LONG_SHORT = 'S') AND T.TRXTYP NOT IN ('1480', '1485'))
                    )
                    OR
                    (
                        (T.BUY_SELL IS NULL)
                        AND
                        (
                            (T.TRXTYP <> '1128') AND 
                            (
                                (T.TRXTYP IN ('1440')) 
                                OR 
                                (
                                    (T.TRXTYP IN ('1455')) 
                                    AND 
                                    (
                                        (T.QTY <> 'N') 
                                        AND 
                                        ((TC.LONG_SHORT <> 'L') AND (T.TRXTYP NOT IN ('1170', '1175')))
                                    )
                                )
                            )
                        )
                    )
                THEN
                    CASE 
                        WHEN (TC.REVFLG = 'N' OR TC.REVFLG IS NULL)
                        THEN
                           - TC.QTY
                        ELSE
                            +TC.QTY
                    END
                END
             ), 0
        ) AS QTY
    FROM 
        TRXCUR TC
    JOIN 
        TRXTYP T ON T.TRXTYP = TC.TRXTYP
    JOIN 
        FNDMAS F ON TC.FUND = F.FUND
    JOIN 
        SECRTY S ON TC.TKR = S.TKR
    LEFT JOIN 
        TRXCUR TRC ON TRC.FUND = TC.FUND AND TC.FIRST_TRX = TRC.TRXCUR_NO AND TC.TRXTYP = '2171'
    LEFT JOIN 
        TRXCUR OPT ON OPT.FUND = TC.FUND AND OPT.TRXCUR_NO = (
            CASE WHEN TC.REVFLG = 'N' THEN TC.OPTION_ID
            ELSE (SELECT OPTION_ID FROM TRXCUR WHERE FUND = TC.FUND AND TRXCUR_NO = TC.REVID AND TC.TRXTYP IN ('1115', '1125', '1135', '1145'))
            END
        )
    LEFT JOIN 
        GANDL G ON G.FUND = TC.FUND AND G.CLOSE_TRX = TC.TRXCUR_NO AND G.CLSDAT = TC.TRADE_DATE
    LEFT JOIN 
        SECRTY S2 ON S2.TKR = OPT.TKR
    WHERE 
        TC.tkr=:tkr AND TC.fund=:fund  
    GROUP BY 
        TC.FUND, TC.TKR, TC.TAXLOT_ID, TC.TRADE_DATE, TC.QTY
) derivedTable
WHERE derivedTable.QTY <> 0
ORDER BY TRADE_DATE
"""
        sql_query = text(query)
        result = connection.execute(sql_query.params(fund=fund, tkr=tkr))
        Qty_data = result.fetchall()
        # Get the column names from the result set
        columns = result.keys()
        # Convert the result into a list of dictionaries
        # Convert the result into a list of dictionaries
        QTY_data_list = [dict(zip(columns, row)) for row in Qty_data]

        # Calculate remaining QTY
        remaining_qty = 0
        for record in QTY_data_list:
            # Convert qty to a float for consistent handling
            qty = float(record['qty'])

            # Calculate remaining qty by adding the current qty to the previous remaining qty
            remaining_qty += qty

            # Add the "remaining QTY" column to the record
            record['remaining_qty'] = remaining_qty

        # Close the connection
        connection.close()

        # Return the modified data with the new "remaining QTY" column
        return jsonify({'data': QTY_data_list})
    except Exception as e:
        # Log the exception stack trace for debugging
        print(f"Error in filter_data_for_fund_and_date_range: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_getCashMovement_blueprint.route('/getCash/<string:fund>/<string:tkr>', methods=['GET'])
def getCashMovement_blueprint(tkr,fund):
    try:
        connection = get_shared_connection()
        query = """
     
     SELECT 
        TC.FUND, 
        TC.TKR, 
        TC.TAXLOT_ID,
        TC.TRADE_DATE,
        TC.price, 
NVL(SUM(
             CASE WHEN (T.BUY_SELL='S')
                  THEN
                    CASE WHEN T.TRXTYP  NOT IN ('1122','1123','1330')
                         THEN
                            CASE WHEN (TC.REVFLG='N' OR TC.REVFLG IS NULL)
                                 THEN
                                      TC.LOCAL_BOOK
                                 ELSE
                                     -TC.LOCAL_BOOK
                            END
                    END
             ELSE
                   CASE WHEN ((T.BUY_SELL IS NULL) AND (T.TRXTYP = '1128'))
                       THEN
                            CASE WHEN (TC.REVFLG='N' OR TC.REVFLG IS NULL)
                                 THEN
                                   TC.LOCAL_BOOK
                 ELSE
                                   -TC.LOCAL_BOOK
                            END
                   END
             END),0)
             - NVL(SUM( CASE
               WHEN T.TRXTYP IN ('1115','1125','1135','1145') THEN
                          CASE WHEN (TC.REVFLG='N' OR TC.REVFLG IS NULL) THEN
                               NVL(ROUND(opt.LOCAL_BOOK*TC.QTY/opt.QTY/NVL(S2.CONV_RATIO, 1), s.lcl_m_decs),0)
                          ELSE
                                -NVL(ROUND(opt.LOCAL_BOOK*TC.QTY/opt.QTY/NVL(S2.CONV_RATIO, 1), s.lcl_m_decs),0)
                          END
               ELSE 0 END),0 )
             -
         NVL(SUM(
            CASE WHEN (T.BUY_SELL = 'S') THEN
                    CASE WHEN (T.TRXTYP IN ('1330')) THEN
                           - TC.LOCAL_BOOK
                   end
            ELSE
               CASE WHEN (T.BUY_SELL = 'B')
                    THEN
                       CASE WHEN (TC.REVFLG='N' OR TC.REVFLG IS NULL)
                            THEN
                                TC.LOCAL_BOOK
                            ELSE
                               -TC.LOCAL_BOOK
                       END
            ELSE
               CASE WHEN (T.BUY_SELL IS NULL AND (T.ACCINC='N'))
                    THEN
            CASE WHEN (T.TRXTYP NOT IN ('1128','1455','2171'))
                             THEN
                                TC.LCL_NETCAS
                        END
               END
            END
            END),0) lcltaxbook
            
    FROM 
        TRXCUR TC
    JOIN 
        TRXTYP T ON T.TRXTYP = TC.TRXTYP
    JOIN 
        FNDMAS F ON TC.FUND = F.FUND
    JOIN 
        SECRTY S ON TC.TKR = S.TKR
    LEFT JOIN 
        TRXCUR TRC ON TRC.FUND = TC.FUND AND TC.FIRST_TRX = TRC.TRXCUR_NO AND TC.TRXTYP = '2171'
    LEFT JOIN 
        TRXCUR OPT ON OPT.FUND = TC.FUND AND OPT.TRXCUR_NO = (
            CASE WHEN TC.REVFLG = 'N' THEN TC.OPTION_ID
            ELSE (SELECT OPTION_ID FROM TRXCUR WHERE FUND = TC.FUND AND TRXCUR_NO = TC.REVID AND TC.TRXTYP IN ('1115', '1125', '1135', '1145'))
            END
        )
    LEFT JOIN 
        GANDL G ON G.FUND = TC.FUND AND G.CLOSE_TRX = TC.TRXCUR_NO AND G.CLSDAT = TC.TRADE_DATE
    LEFT JOIN 
        SECRTY S2 ON S2.TKR = OPT.TKR
    WHERE 
        TC.tkr=:tkr  AND TC.fund=:fund
    GROUP BY 
        TC.FUND, TC.TKR, TC.TAXLOT_ID, TC.TRADE_DATE, TC.QTY ,TC.price 
     order by trade_date 

"""
        sql_query = text(query)
        result = connection.execute(sql_query.params(fund=fund, tkr=tkr))
        Qty_data = result.fetchall()
        # Get the column names from the result set
        columns = result.keys()
        Cash_data_list = [dict(zip(columns, row)) for row in Qty_data]

        # Close the connection
        connection.close()
        # Return the modified data with the new "remaining QTY" column
        return jsonify({'data': Cash_data_list})
    except Exception as e:
        # Log the exception stack trace for debugging
        print(f"Error in filter_data_for_fund_and_date_range: {str(e)}")
        return jsonify({'error': str(e)}), 500

auth_bp = Blueprint("auth", __name__)
@auth_bp.get("/whoami")
@jwt_required()
def whoami():
    return jsonify(
        {
            "message": "message",
            "user_details": {
                "username": current_user.username,
                "email": current_user.email,
            },
        }
    )
@api_getUsrFnd_blueprint.route('/getUsrFnd', methods=['POST'])
def api_getUsrFnd():
    try:
        # Get UserId from the JSON data
        user_id = request.json.get('USER_ID')

        if user_id is None:
            return jsonify({'error': 'UserId is required in the JSON payload'}), 400

        # Query Usrfnd records based on UserId
        usrfnd_records = Usrfnd.query.filter_by(USER_ID=user_id).order_by(asc(Usrfnd.FUND)).all()

        fnd_list = [record.FUND for record in usrfnd_records]

        # Query FNDMAS records based on FND list and INACTIVE status
        fndmas_records = Fndmas.query.filter(Fndmas.FUND.in_(fnd_list), Fndmas.INACTIVE == 'N').all()

        # Convert records to a list of dictionaries
        fndmas_list = [record.to_dict() for record in fndmas_records]

        # Create and return the JSON response
        json_result = {'data': fndmas_list}
        return jsonify(json_result)

    except Exception as e:
        # Log the exception stack trace for debugging
        print(f"Error in api_getUsrFnd: {str(e)}")
        return jsonify({'error': str(e)}), 500
