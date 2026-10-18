import os
import xarray as xr
from app.scripts._global import GLOBAL_CONFIG

xr.set_options(use_new_combine_kwarg_defaults=True)

def read_seasfcst_flexible_data(params):
    obs = read_seasfcst_obs(params)
    mean, fcst_times = read_seasfcst_mean(params)
    var = read_seasfcst_var(params)

    fcst_ds = (
        xr.combine_by_coords(mean)
        .merge(xr.combine_by_coords(var))
    )
    return obs, fcst_ds, fcst_times

def read_seasfcst_anomaly_data(params):
    obs = read_seasfcst_obs(params)
    mean, fcst_times = read_seasfcst_mean(params)
    obs_mean = obs.mean(dim='T')
    anom = mean - obs_mean
    return anom, fcst_times

def read_seasfcst_obs(params):
    fcst_path = _get_seasfcst_path(params)
    obs_path = os.path.join(fcst_path, 'obs.nc')
    if not os.path.exists(obs_path):
        raise ValueError('Observation file "obs.nc" not found.')

    obs = xr.open_dataarray(obs_path)
    obs = obs.drop_vars(['Ti', 'Tf'])
    return obs

def read_seasfcst_mean(params):
    fcst_path = _get_seasfcst_path(params)
    mean_file = f'MME_deterministic_forecast_{params["year"]}.nc'
    mean_path = os.path.join(fcst_path, mean_file)
    if not os.path.exists(mean_path):
        raise ValueError(
            f'Deterministic forecast file {mean_file} not found.'
        )

    mean = xr.open_dataarray(mean_path)
    fcst_times = {
        'time': _get_seasfcst_time(mean['T']),
        'start': _get_seasfcst_time(mean.Ti),
        'end': _get_seasfcst_time(mean.Tf),
        'issued': _get_seasfcst_time(mean.S)
    }
    mean = mean.drop_vars(['S', 'Ti', 'Tf', 'T'])
    return mean, fcst_times

def read_seasfcst_var(params):
    fcst_path = _get_seasfcst_path(params)
    var_file = f'MME_forecast_prediction_error_variance_{params["year"]}.nc'
    var_path = os.path.join(fcst_path, var_file)
    if not os.path.exists(var_path):
        raise ValueError(
            f'Forecast prediction error variance file {var_file} not found.'
        )

    var = xr.open_dataarray(var_path)
    var = var.drop_vars(['S', 'Ti', 'Tf', 'T'])
    return var

def read_seasfcst_proba(params):
    fcst_path = _get_seasfcst_path(params)
    proba_file = f'MME_probabilistic_forecast_{params["year"]}.nc'
    proba_path = os.path.join(fcst_path, proba_file)
    if not os.path.exists(proba_path):
        raise ValueError(
            f'Probabilistic_forecast file {proba_file} not found.'
        )

    proba = xr.open_dataarray(proba_path)
    proba = proba.drop_vars(['S', 'Ti', 'Tf', 'T'])
    return proba

def _get_seasfcst_path(params):
    fcst_dir = GLOBAL_CONFIG['forecast_data']
    fcst_dir = fcst_dir['seasonal'][params['variable']]
    return os.path.join(
        fcst_dir,
        params['year'],
        params['issued'],
        params['target']
    )

def _get_seasfcst_time(time):
    tmp = time.values
    tmp = tmp.astype('datetime64[D]')[0]
    return tmp.astype(str).item()
