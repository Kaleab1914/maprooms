import os
from threading import RLock

import xarray as xr
from app.scripts._global import GLOBAL_CONFIG

xr.set_options(use_new_combine_kwarg_defaults=True)

# The netCDF4/HDF5 stack used by this application can segfault when Flask
# serves two forecast requests concurrently.  Keep access serialized and load
# each file into memory so no lazy reads escape the protected section.
_NETCDF_READ_LOCK = RLock()

def _load_dataarray(path):
    with _NETCDF_READ_LOCK:
        data = xr.open_dataarray(path)
        try:
            data.load()
        finally:
            data.close()
    return data

def read_seasfcst_flexible_data(params):
    obs = read_seasfcst_obs(params)
    mean = read_seasfcst_mean(params)
    var = read_seasfcst_var(params)
    fcst_ds = (
        xr.combine_by_coords(mean)
        .merge(xr.combine_by_coords(var))
    )
    return obs, fcst_ds

def read_seasfcst_flexible_point(params):
    obs_da, fcst_ds = read_seasfcst_flexible_data(params)
    obs, fcst = _get_point_data(
        obs_da, fcst_ds, params['pointsList'][0]
    )
    return obs, fcst

def read_seasfcst_anomaly_data(params):
    obs = read_seasfcst_obs(params)
    mean = read_seasfcst_mean(params)
    obs_mean = obs.mean(dim='T')
    return mean - obs_mean

def read_seasfcst_obs(params):
    fcst_path = _get_seasfcst_path(params)
    obs_path = os.path.join(fcst_path, 'obs.nc')
    if not os.path.exists(obs_path):
        raise ValueError('Observation file "obs.nc" not found.')
    return _load_dataarray(obs_path)

def read_seasfcst_mean(params):
    fcst_path = _get_seasfcst_path(params)
    mean_file = f'MME_deterministic_forecast_{params["year"]}.nc'
    mean_path = os.path.join(fcst_path, mean_file)
    if not os.path.exists(mean_path):
        raise ValueError(
            f'Deterministic forecast file {mean_file} not found.'
        )
    return _load_dataarray(mean_path)

def read_seasfcst_var(params):
    fcst_path = _get_seasfcst_path(params)
    var_file = f'MME_forecast_prediction_error_variance_{params["year"]}.nc'
    var_path = os.path.join(fcst_path, var_file)
    if not os.path.exists(var_path):
        raise ValueError(
            f'Forecast prediction error variance file {var_file} not found.'
        )
    return _load_dataarray(var_path)

def read_seasfcst_proba(params):
    fcst_path = _get_seasfcst_path(params)
    proba_file = f'MME_probabilistic_forecast_{params["year"]}.nc'
    proba_path = os.path.join(fcst_path, proba_file)
    if not os.path.exists(proba_path):
        raise ValueError(
            f'Probabilistic_forecast file {proba_file} not found.'
        )
    return _load_dataarray(proba_path)

def get_seasfcst_times(params):
    mean = read_seasfcst_mean(params)
    return {
        'time': _get_seasfcst_time(mean['T']),
        'start': _get_seasfcst_time(mean.Ti),
        'end': _get_seasfcst_time(mean.Tf),
        'issued': _get_seasfcst_time(mean.S)
    }

def _get_seasfcst_path(params):
    fcst_dir = GLOBAL_CONFIG['forecast_data']['seasonal']
    return os.path.join(
        fcst_dir[params['variable']]['dir'],
        params['year'],
        params['issued'],
        params['target']
    )

def _get_seasfcst_time(time):
    tmp = time.values
    tmp = tmp.astype('datetime64[D]')[0]
    return tmp.astype(str).item()

def _get_point_data(obs_da, fcst_ds, loc):
    obs = obs_da.sel(
        X=float(loc['lon']),
        Y=float(loc['lat']),
        method='nearest'
    )
    fcst = fcst_ds.sel(
        X=float(loc['lon']),
        Y=float(loc['lat']),
        method='nearest'
    )
    return obs, fcst
