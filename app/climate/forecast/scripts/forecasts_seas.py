import numpy as np
import xarray as xr
from scipy import stats
import warnings

from .read_forecasts import (
    read_seasfcst_flexible_data,
    read_seasfcst_anomaly_data,
    read_seasfcst_mean,
    read_seasfcst_proba
)
from app.scripts.imagepng import (
    create_imagePng,
    terciles_imagePng
)
from app.scripts.colorbar import check_invalid_colors
from app.misc.scripts.blank_data import (
    blank_numpy_dict,
    blank_xarray_dataarray
)

def climate_forecast_seas_data(params):
    check = check_invalid_colors(params['colorbar'])
    if check['status'] == -1: return check

    if params['forecast'] == 'flexible':
        if params['parameter'] in ['probExc', 'probNoExc']:
            data = get_seasonal_probability_map(params)
        elif params['parameter'] in ['TotRain', 'MeanTemp']:
            data = get_seasonal_deterministic_map(params)
        elif params['parameter'] in ['AnomRain', 'AnomTemp']:
            data = get_seasonal_anomaly_map(params)
        else:
            return {
                'status': -1,
                'message': f'Unknown parameter: {params["parameter"]}'
            }

        if params['colorbar']['color_type'] == 'preset':
            map_png = create_imagePng(
                data,
                breaks=params['colorbar']['break_cbar'],
                color_name=params['colorbar']['color_cbar'],
                colors_ext=params['colorbar']['color_ext']
            )
        else:
            map_png = create_imagePng(
                data,
                breaks=params['colorbar']['break_cbar'],
                colors=params['colorbar']['color_cbar'],
                colors_ext=params['colorbar']['color_ext']
            )
        titles = {
            'probExc': 'Probability of exceeding',
            'probNoExc': 'Probability of non-exceeding',
            'TotRain': 'Total rainfall (mm)',
            'AnomRain': 'Rainfall anomaly (mm)',
            'MeanTemp': 'Mean temperature (°C)',
            'AnomTemp': 'Mean temperature anomaly (°C)'
        }
        map_png['ckeys']['title'] = titles[params['parameter']]
    else:
        data = get_seasonal_terciles_map(params)
        map_png = terciles_imagePng(data)

    map_png['date'] = f"{params['target']} {params['year']}"
    return {'status': 0, 'data': map_png}


def get_seasonal_probability_map(params):
    obs_da, fcst_ds, _ = read_seasfcst_flexible_data(params)
    data = seasonal_probability_map(
        obs_da, fcst_ds,
        params['probaType'],
        params['probaThres']
    )
    data = blank_numpy_dict(data, buffer=True)

    if params['parameter'] == 'probExc':
        data['data'] = 1 - data['data']

    # breaks = [
    #     round(x.item(), 1)
    #     for x in np.arange(0.1, 1.0, 0.1)
    # ]
    return data

def get_seasonal_deterministic_map(params):
    mean, _ = read_seasfcst_mean(params)
    mean = blank_xarray_dataarray(mean)
    return {
        'lon': mean['X'],
        'lat': mean['Y'],
        'data': mean.squeeze().to_numpy()
    }

def get_seasonal_anomaly_map(params):
    anom, _ = read_seasfcst_anomaly_data(params)
    anom = blank_xarray_dataarray(anom)
    return {
        'lon': anom['X'],
        'lat': anom['Y'],
        'data': anom.squeeze().to_numpy()
    }

def get_seasonal_terciles_map(params):
    da = read_seasfcst_proba(params)
    da = da.transpose('C', 'T', 'Y', 'X').isel(T=0)
    data = {
        'lon': da.X.values,
        'lat': da.Y.values,
        'winner': np.argmax(da.values, axis=0),
        'proba': np.max(da.values, axis=0)
    }
    dims = {'lon': 'lon', 'lat': 'lat', 'data': 'winner'}
    data = blank_numpy_dict(data, dims=dims, buffer=True)
    data['proba'][np.isnan(data['winner'])] = np.nan
    return data

def seasonal_probability_map(
    obs_da: xr.DataArray,
    fcst_ds: xr.Dataset,
    proba_type: str,
    threshold: float
) -> dict:
    if proba_type == 'percentile':
        obs_mean = obs_da.mean(dim='T')
        with warnings.catch_warnings():
            warnings.simplefilter(
                'ignore', category=RuntimeWarning
            )
            obs_std = obs_da.std(dim='T')
        obs_ppf = xr.apply_ufunc(
            stats.norm.ppf,
            float(threshold)/100,
            kwargs={
                'loc': obs_mean,
                'scale': obs_std
            }
        )
        ## precipitation data
        obs_ppf = obs_ppf.clip(min=0)
    else:
        obs_ppf = float(threshold)

    fcst_dof = obs_da['T'].size - 1
    fcst_mean = fcst_ds['deterministic']
    fcst_var = fcst_ds['prediction_error_variance']
    fcst_cdf = xr.apply_ufunc(
        stats.t.cdf,
        obs_ppf,
        fcst_dof,
        kwargs={
            'loc': fcst_mean,
            'scale': np.sqrt(fcst_var)
        }
    )
    return {
        'lon': fcst_ds['X'].values,
        'lat': fcst_ds['Y'].values,
        'data': fcst_cdf
    }
