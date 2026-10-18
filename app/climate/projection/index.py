
from flask import Blueprint, render_template, request, session
from flask import current_app as app
from threading import Lock
import json
import config

from .scripts.projection_sp import climate_projection_sp_data
from .scripts.projection_ts import (
    climate_projection_ts_pdf,
    climate_projection_ts_series
)

from .scripts.model_agreement import (
    get_climate_projection_agreement_sp_data,
    climate_projection_agreement_sp_data,
)


climate_projection = Blueprint(
    'climate_projection',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/static/climate_projection',
)

matplotlib_render_lock = Lock()

dataUser = dict()


@climate_projection.before_request
def before_request():
    global dataUser

    if 'logged_in' not in session:
        dataUser = {'uid': -1}
    else:
        if session['logged_in']:
            dataUser = session['data']
        else:
            dataUser = {'uid': -1}


@climate_projection.route('/climate_projection_seasonal_map', methods=['POST'])
def climate_projection_seasonal_map():
    params = request.get_json()

    try:
        with matplotlib_render_lock:
            result = climate_projection_sp_data(params)

        return json.dumps(result)

    except (KeyError, TypeError, ValueError, FileNotFoundError) as exc:
        return json.dumps({
            'status': -1,
            'message': str(exc)
        })

    except Exception:
        app.logger.exception('Seasonal projection map failed')

        return json.dumps({
            'status': -1,
            'message': 'Unable to calculate the seasonal change map.'
        })



@climate_projection.route('/climate_projection_pdf', methods=['POST'])
def climate_projection_pdf():
    params = request.get_json()

    try:
        result = climate_projection_ts_pdf(params)
        return json.dumps(result, allow_nan=False)

    except (KeyError, IndexError, TypeError, ValueError, FileNotFoundError) as exc:
        return json.dumps({
            'status': -1,
            'message': str(exc)
        })

    except Exception:
        app.logger.exception('Projection PDF calculation failed')
        return json.dumps({
            'status': -1,
            'message': 'Unable to calculate the projection PDF.'
        })



@climate_projection.route(
    '/climate_projection_series',
    methods=['POST']
)
def climate_projection_series():
    params = request.get_json()

    try:
        result = climate_projection_ts_series(params)

        return json.dumps(result, allow_nan=False)

    except (
        KeyError,
        IndexError,
        TypeError,
        ValueError,
        FileNotFoundError
    ) as exc:
        return json.dumps({
            'status': -1,
            'message': str(exc)
        })

    except Exception:
        app.logger.exception(
            'Projection time-series calculation failed'
        )

        return json.dumps({
            'status': -1,
            'message': (
                'Unable to calculate the projection time series.'
            )
        })



@climate_projection.route(
    '/climate_projection_agreement_map',
    methods=['POST'],
)
def climate_projection_agreement_map():
    try:
        params = request.get_json()

        # Calculate outside the Matplotlib rendering lock.
        data = get_climate_projection_agreement_sp_data(params)

        with matplotlib_render_lock:
            result = climate_projection_agreement_sp_data(data)

        return json.dumps(result, allow_nan=False)

    except (KeyError, TypeError, ValueError, FileNotFoundError) as exc:
        return json.dumps({
            'status': -1,
            'message': str(exc),
        })

    except Exception:
        app.logger.exception('Projection model agreement failed')

        return json.dumps({
            'status': -1,
            'message': 'Unable to calculate the model agreement map.',
        })


