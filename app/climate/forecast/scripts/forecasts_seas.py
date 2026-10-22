import numpy as np
import xarray as xr
from scipy import stats
import warnings

from .read_forecasts import (
    read_seasfcst_flexible_data,
    read_seasfcst_anomaly_data,
    read_seasfcst_mean,
    read_seasfcst_proba,
    read_seasfcst_flexible_point
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
        units = None
        pthres = None
        if params['parameter'] in ['probExc', 'probNoExc']:
            data = get_seasonal_probability_map(params)

            pthres = params['probaThres']
            if params['probaType'] == 'percentile':
                units = '%-ile'
            else:
                var_units = {'rainfall': 'mm', 'temperature': '°C'}
                units = var_units[params['variable']]
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
            'probExc': f"Probability of exceeding {pthres} {units}",
            'probNoExc': f"Probability of non-exceeding {pthres} {units}",
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

def climate_forecast_seas_df(params):
    if params['chartType'] == 'probability':
        obs, fcst = read_seasfcst_flexible_point(params)
        data = seasonal_probability_functions(obs, fcst, params['variable'])
        return {'status': 0, 'data': data}
    elif params['chartType'] == 'tercile':
        fcst_da = read_seasfcst_proba(params)
        data = seasonal_probability_tercile(
            fcst_da,
            params['pointsList'][0]
        )
        return {'status': 0, 'data': data}
    else:
        return {'status': -1, 'message': 'Unknown chart type'}

def get_seasonal_probability_map(params):
    obs_da, fcst_ds = read_seasfcst_flexible_data(params)
    data = seasonal_probability_map(
        obs_da, fcst_ds,
        params['probaType'],
        params['probaThres'],
        params['variable']
    )
    data = blank_numpy_dict(data, buffer=True)

    if params['parameter'] == 'probExc':
        data['data'] = 1 - data['data']
    return data

def get_seasonal_deterministic_map(params):
    mean = read_seasfcst_mean(params)
    mean = blank_xarray_dataarray(mean)
    return {
        'lon': mean['X'],
        'lat': mean['Y'],
        'data': mean.squeeze().to_numpy()
    }

def get_seasonal_anomaly_map(params):
    anom = read_seasfcst_anomaly_data(params)
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
    threshold: float,
    variable: str
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
        if variable == 'rainfall':
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

def seasonal_probability_functions(
    obs: xr.DataArray,
    fcst: xr.Dataset,
    variable: str
) -> dict:
    quantiles = np.arange(1, 512) / 512
    quantiles = xr.DataArray(
        quantiles,
        dims='percentile',
        coords={
            'percentile': quantiles
        }
    )
    obs_q, obs_mu = xr.broadcast(
        quantiles,
        obs.mean(dim='T')
    )
    obs_stddev = obs.std(dim='T')
    obs_ppf = xr.apply_ufunc(
        stats.norm.ppf,
        obs_q,
        kwargs={
            'loc': obs_mu,
            'scale': obs_stddev
        },
    ).rename('obs_ppf')
    obs_quant = obs.quantile(quantiles, dim='T')

    fcst_dof = obs['T'].size - 1
    fcst_mean = fcst['deterministic']
    fcst_var = fcst['prediction_error_variance']

    fcst_q, fcst_mu = xr.broadcast(
        quantiles, fcst_mean
    )
    fcst_ppf = xr.apply_ufunc(
        stats.t.ppf,
        fcst_q,
        fcst_dof,
        kwargs={
            'loc': fcst_mu,
            'scale': np.sqrt(fcst_var)
        }
    ).rename('fcst_ppf')

    if variable == 'rainfall':
        fcst_ppf = fcst_ppf.clip(min=0)
        obs_ppf = obs_ppf.clip(min=0)

    fcst_pdf = xr.apply_ufunc(
        stats.t.pdf,
        fcst_ppf,
        fcst_dof,
        kwargs={
            'loc': fcst_mean,
            'scale': np.sqrt(fcst_var)
        }
    ).rename('fcst_pdf')

    obs_pdf = xr.apply_ufunc(
        stats.norm.pdf,
        obs_ppf,
        kwargs={
            'loc': obs_mu,
            'scale': obs_stddev
        }
    ).rename('obs_pdf')

    probaExc = fcst_ppf['percentile'] * -1 + 1
    probaExc = probaExc.squeeze().values * 100

    data = {}
    data['cdf'] = {
        'proba': probaExc.tolist(),
        'forecast': fcst_ppf.squeeze().values.tolist(),
        'obs_empirical': obs_quant.squeeze().values.tolist(),
        'obs_parametric': obs_ppf.squeeze().values.tolist()
    }
    data['cdf']['info'] = {
        'variable': 'Total Rainfall',
        'units': 'mm',
        'ylab': 'Probability of exceeding'
    }
    data['pdf'] = {
        'proba': probaExc.tolist(),
        'forecast': {
            'x': fcst_ppf.squeeze().values.tolist(),
            'y': fcst_pdf.squeeze().values.tolist()
        },
        'observation': {
            'x': obs_ppf.squeeze().values.tolist(),
            'y': obs_pdf.squeeze().values.tolist()
        }
    }
    data['pdf']['info'] = {
        'variable': 'Total Rainfall',
        'units': 'mm',
        'ylab': 'Probability density'
    }
    return data

def seasonal_probability_tercile(
    fcst_ter: xr.DataArray,
    loc: dict
) -> dict:
    fcst = fcst_ter.sel(
        X=float(loc['lon']),
        Y=float(loc['lat']),
        method='nearest'
    )
    proba = fcst.values.squeeze().tolist()
    category = fcst['C'].values.tolist()
    data = {}
    data['tercile'] = {c: p for c, p in zip(category, proba)}
    data['info'] = {
        'xlab': 'Tercile categories',
        'ylab': 'Tercile probabilities',
        'units': '%',
        'categories': {
            '1': 'Below Normal',
            '2': 'Near Normal', 
            '3': 'Above Normal'
        }
    }
    return data
