import json

from threading import Lock

from flask import Blueprint, request, session
from flask import current_app as app

from .scripts.wasp_data import (
    health_wasp_coverage_data,
)

from .scripts.wasp_sp import (
    health_wasp_sp_data,
)

from .scripts.wasp_ts import (
    health_wasp_ts_data,
)

from app.scripts._cache import (
    cache_data_functions,
    hash_pamars_clim,
)


health_malaria = Blueprint(
    "health_malaria",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static/health_malaria",
)

wasp_render_lock = Lock()
wasp_series_lock = Lock()

dataUser = {}


@health_malaria.before_request
def before_request():
    global dataUser

    if "logged_in" not in session:
        dataUser = {"uid": -1}
    elif session["logged_in"]:
        dataUser = session["data"]
    else:
        dataUser = {"uid": -1}


def _health_wasp_response(function):
    try:
        params = request.get_json()

        if not isinstance(params, dict):
            raise ValueError(
                "Expected a JSON request object."
            )

        result = function(params)

        return app.response_class(
            json.dumps(
                result,
                allow_nan=False,
            ),
            mimetype="application/json",
        )

    except (
        KeyError,
        IndexError,
        TypeError,
        ValueError,
        FileNotFoundError,
    ) as exc:
        return {
            "status": -1,
            "message": str(exc),
        }

    except Exception:
        app.logger.exception(
            "Health WASP request failed"
        )

        return {
            "status": -1,
            "message": "Unable to calculate WASP.",
        }


@health_malaria.route(
    "/health_wasp_coverage",
    methods=["POST"],
)
def health_wasp_coverage():
    return _health_wasp_response(
        health_wasp_coverage_data
    )


@health_malaria.route(
    "/health_wasp_map",
    methods=["POST"],
)
def health_wasp_map():
    def calculate(params):
        with wasp_render_lock:
            return health_wasp_sp_data(params)

    return _health_wasp_response(calculate)


@health_malaria.route(
    "/health_wasp_series",
    methods=["POST"],
)
def health_wasp_series():
    params = request.get_json()

    if not isinstance(params, dict):
        return {
            "status": -1,
            "message": "Expected a JSON request object.",
        }

    try:
        with wasp_series_lock:
            return cache_data_functions(
                health_wasp_ts_data,
                hash_pamars_clim,
                params,
            )

    except Exception as exc:
        app.logger.exception("Health WASP series failed")

        return {
            "status": -1,
            "message": str(exc),
        }

        