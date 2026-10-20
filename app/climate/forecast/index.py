from flask import (
    Blueprint,
    render_template,
    request,
    session
)
from flask import current_app as app
import json

from .scripts.forecasts_data import get_seasonal_forecast_files
from .scripts.forecasts_seas import (
    climate_forecast_seas_data,
    climate_forecast_seas_df
)

climate_forecast = Blueprint(
    'climate_forecast',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/static/climate_forecast',
)

dataUser = dict()
@climate_forecast.before_request
def before_request():
    global dataUser
    if 'logged_in' not in session:
        dataUser = {'uid': -1}
    else:
        if session['logged_in']:
            dataUser = session['data']
        else:
            dataUser = {'uid': -1}

@climate_forecast.route('/get_seasonal_forecasts_data')
def get_seasonal_forecasts_data():
    variable = request.args.get('variable')
    try:
        return json.dumps(
            get_seasonal_forecast_files(variable)
        )
    except Exception as e:
        return json.dumps({'status': -1, 'message': str(e)})

@climate_forecast.route('/climate_forecast_seas_map', methods=['POST'])
def climate_forecast_seas_map():
    params = request.get_json()
    try:
        map_data = climate_forecast_seas_data(params)
        return json.dumps(map_data)
    except Exception as e:
        return json.dumps({'status': -1, 'message': str(e)})

@climate_forecast.route('/climate_forecast_seas_proba', methods=['POST'])
def climate_forecast_seas_proba():
    params = request.get_json()
    try:
        proba_data = climate_forecast_seas_df(params)
        return json.dumps(proba_data)
    except Exception as e:
        return json.dumps({'status': -1, 'message': str(e)})
