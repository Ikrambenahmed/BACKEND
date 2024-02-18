from app.PricesPrediction.PreditionModel import api_predictPrices_blueprint, api_createModel_blueprint, \
    api_highest_prices_blueprint
from app.infrastructure.ConnectDB import api_Logout_blueprint
from app.infrastructure.login import api_SetDatabase_blueprint, api_TestConnection_blueprint, api_ConnectToDB_blueprint, \
    api_Login_blueprint
from app.portfolio.FundDetails import api_getFndmas_blueprint, api_getNAVHSTFndmas_blueprint, \
    api_getALLFndmas_blueprint, api_getALLPrices_blueprint, api_getQtyMovement_blueprint, api_getCashMovement_blueprint, \
    auth_bp, api_getUsrFnd_blueprint
from app.portfolio.OpnposDetails import api_getOpnpos_blueprint, api_getTotals_blueprint, api_AssetAllocation_blueprint
from app.workflow.workflow import api_getworkflow_blueprint, api_getOptevtRules_blueprint


def initialize_blueprints(app):
    app.register_blueprint(api_Login_blueprint)
    app.register_blueprint(api_SetDatabase_blueprint)
    app.register_blueprint(api_predictPrices_blueprint, url_prefix='/api/')
    app.register_blueprint(api_getFndmas_blueprint, url_prefix='/api/')
    app.register_blueprint(api_getNAVHSTFndmas_blueprint, url_prefix='/api/')
    app.register_blueprint(api_getworkflow_blueprint, url_prefix='/api/')
    app.register_blueprint(api_getALLFndmas_blueprint, url_prefix='/api/')
    app.register_blueprint(api_getOpnpos_blueprint, url_prefix='/api/')
    app.register_blueprint(api_getALLPrices_blueprint, url_prefix='/api/')
    app.register_blueprint(api_createModel_blueprint, url_prefix='/api/')
    app.register_blueprint(api_getQtyMovement_blueprint, url_prefix='/api/')
    app.register_blueprint(api_getOptevtRules_blueprint, url_prefix='/api/')
    app.register_blueprint(api_getCashMovement_blueprint, url_prefix='/api/')
    app.register_blueprint(api_TestConnection_blueprint, url_prefix='/api/')
    app.register_blueprint(api_Logout_blueprint)
    app.register_blueprint(api_ConnectToDB_blueprint, url_prefix='/api/')
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_getUsrFnd_blueprint,url_prefix='/api/')
    app.register_blueprint(api_getTotals_blueprint,url_prefix='/api/')
    app.register_blueprint(api_AssetAllocation_blueprint,url_prefix='/api/')
    app.register_blueprint(api_highest_prices_blueprint,url_prefix='/api/')

























