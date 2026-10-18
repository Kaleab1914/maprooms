import os
from app.scripts._global import GLOBAL_CONFIG
from .parse_forecasts import parse_seasonal_forecast_files

def get_seasonal_forecast_files(variable):
    fcst_dir = GLOBAL_CONFIG['forecast_data']['seasonal'][variable]
    if not os.path.exists(fcst_dir):
        return {
            'status': -1,
            'message': f'No {variable} seasonal forecast found.'
        }
    try:
        fcst_seas = parse_seasonal_forecast_files(fcst_dir)
        return {'status': 0, 'data': fcst_seas}
    except Exception as e:
        return {'status': -1, 'message': str(e)}
