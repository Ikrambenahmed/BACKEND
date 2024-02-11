from app.models.TRXCUR import TRXCUR

from flask import jsonify, Blueprint
import joblib
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from datetime import datetime

api_getALLTRXCUR_blueprint = Blueprint('api_getALLTRXCUR', __name__)
api_getTRXCURFUND_blueprint = Blueprint('api_getTRXCURFUND', __name__)
api_count_trx_occurrences_blueprint = Blueprint('api_count_trx_occurrences', __name__)
api_calculate_likelihood_blueprint=Blueprint('api_calculate_likelihood', __name__)
api_rank_trxtyps_blueprint=Blueprint('api_rank_trxtyps', __name__)


# API endpoint for loading historical data
@api_getALLTRXCUR_blueprint.route('/load_historical_data', methods=['GET'])
def load_historical_data():
    try:
        historical_data = TRXCUR.query.all()
        return jsonify({'historical_data': [transaction.serialize() for transaction in historical_data]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API endpoint for filtering data for a specific FUND
@api_getTRXCURFUND_blueprint.route('/filter_data_for_fund/<target_fund>', methods=['GET'])
def filter_data_for_fund(target_fund):
    try:
        fund_data = TRXCUR.query.filter_by(FUND=target_fund).all()
        return jsonify({'fund_data': [transaction.serialize() for transaction in fund_data]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API endpoint for counting occurrences of TRXTYP on Mondays for a specific FUND
@api_count_trx_occurrences_blueprint.route('/count_trx_occurrences/<target_fund>', methods=['GET'])
def count_trx_occurrences(target_fund):
    try:
        fund_data = TRXCUR.query.filter_by(FUND=target_fund).all()

        trx_counts = {}
        for transaction in fund_data:
            if datetime.strptime(transaction.TRADE_DATE, "%m/%d/%Y").weekday() == 0:  # Monday
                trx_typ = transaction.TRXTYP
                trx_counts[trx_typ] = trx_counts.get(trx_typ, 0) + 1

        return jsonify({'trx_counts': trx_counts})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API endpoint for calculating likelihood of TRXTYP on Mondays for a specific FUND
@api_calculate_likelihood_blueprint.route('/calculate_likelihood/<target_fund>', methods=['GET'])
def calculate_likelihood(target_fund):
    try:
        fund_data = TRXCUR.query.filter_by(FUND=target_fund).all()

        total_entries_per_trx = {trx_typ: 0 for trx_typ in set([transaction.TRXTYP for transaction in fund_data])}

        # Count total occurrences of each TRXTYP
        for transaction in fund_data:
            trx_typ = transaction.TRXTYP
            total_entries_per_trx[trx_typ] += 1

        # Count occurrences on Mondays and calculate likelihood
        trx_counts = {}
        for transaction in fund_data:
            if datetime.strptime(transaction.TRADE_DATE, "%m/%d/%Y").weekday() == 0:  # Monday
                trx_typ = transaction.TRXTYP
                trx_counts[trx_typ] = trx_counts.get(trx_typ, 0) + 1

        likelihoods = {trx_typ: trx_counts[trx_typ] / total_entries_per_trx[trx_typ] for trx_typ in trx_counts}

        return jsonify({'likelihoods': likelihoods})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API endpoint for ranking TRXTYPs based on likelihood for a specific FUND
@api_rank_trxtyps_blueprint.route('/rank_trxtyps/<target_fund>', methods=['GET'])
def rank_trxtyps(target_fund):
    try:
        likelihoods = calculate_likelihood(target_fund)
        ranked_trxtyps = sorted(likelihoods.items(), key=lambda x: x[1], reverse=True)
        return jsonify({'ranked_trxtyps': ranked_trxtyps})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

