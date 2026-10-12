import json
import numpy as np
from datetime import datetime

from app.dst_api.scripts import (
    download_rawdata,
    extract_climdata,
    download_analysis
)
from app.misc.scripts.tseries_dates import format_tseries_dates
from app.scripts.util import pretty
from app.scripts.dial_plot import draw_dial_image

def climate_monitoring_ts_spei(params):
    data_spei = get_monitoring_ts_spei(params)
    if data_spei['status'] != 0: return data_spei
    values = data_spei['data']['values']
    time = data_spei['data']['time']
    info = data_spei['data']['info']

    if ~np.all(np.isnan(values)):
        vmin = np.nanmin(values)
        vmax = np.nanmax(values)
        val_max = np.maximum(np.abs(vmin), np.abs(vmax))
        breaks = pretty(-val_max, val_max, 14).tolist()
        ylim = np.array([breaks[0], breaks[-1]])
        ylim = ylim + ((ylim[1] - ylim[0]) * 0.01) * np.array([-1, 1])
        values = np.where(np.isnan(values), None, values)
        data = {
            'time': time,
            'values': values.tolist(),
            'info': info,
            'yrange': ylim.tolist(),
            'yticks': breaks
        }

        return {'status': 0, 'data': data}
    else:
        if params['geomExtract'] == 'points':
            lon = info['geom']['lon']
            lat = info['geom']['lat']
            crd = f'point (Longitude: {lon}, Latitude: {lat})'
        else:
            crd = f'polygon ({info['geom']['name']})'

        msg = f'{info['var']['type']}: All data are missing for {crd}'
        return {'status': -1, 'message': msg}

def climate_monitoring_dial_spei(params):
    data_spei = get_monitoring_ts_spei(params)
    if data_spei['status'] != 0: return data_spei
    spei_class = spei_dial_classification(data_spei['data'])

    text_color = 'black'
    if 'theme' in params:
        if params['theme'] == 'dark':
            text_color = 'white'

    img_png = draw_dial_image(
        spei_class,
        text_color,
        figsize=(8.6, 6.2)
    )
    data = {
        'info': data_spei['data']['info'],
        'png': img_png
    }
    return {'status': 0, 'data': data}

def spei_dial_classification(spei):
    spei_class = {
        'definition': [
            {'color': '#b22222', 'label': 'Extremely', 'score': 0, 'state': 'Extremely Dry'},
            {'color': '#d2691e', 'label': 'Severely', 'score': 1, 'state': 'Severely Dry'},
            {'color': '#f5deb3', 'label': 'Moderately', 'score': 2, 'state': 'Moderately Dry'},
            {'color': '#f5f5f5', 'label': 'Normal', 'score': 3, 'state': 'Near Normal'},
            {'color': '#98fb98', 'label': 'Moderately', 'score': 4, 'state': 'Moderately Wet'},
            {'color': '#3cb371', 'label': 'Severely', 'score': 5, 'state': 'Severely Wet'},
            {'color': '#14713d', 'label': 'Extremely', 'score': 6, 'state': 'Extremely Wet'}
        ]
    }

    tscale = int(spei['info']['time_scale'])
    last_val = spei['values'][-1]
    last_date = spei['time'][-1]

    spei_breaks = np.array(spei['info']['spei_breaks'])
    spei_class['score'] = int(
        np.searchsorted(
            spei_breaks, last_val, side='right'
        )
    )

    if spei['info']['time_res'] == 'dekadal':
        txt = 'dekad'
        this_date = datetime.strptime(last_date, '%Y-%m-%d')
        dekad = min((this_date.day - 1) // 10 + 1, 3)
        obs_date = f"Dekad-{dekad} {this_date.strftime('%B %Y')}"

    if spei['info']['time_res'] == 'monthly':
        txt = 'month'
        if tscale > 1:
            txt = f'{txt}s'
        obs_date = (
            datetime.strptime(last_date, '%Y-%m-%d')
            .strftime('%B %Y')
        )

    spei_class['left_text'] = obs_date
    s = spei['info']['var']['type'].upper()
    spei_class['right_text'] = f'{s} {tscale}-{txt}'
    spei_class['left_title'] = 'Dry'
    spei_class['right_title'] = 'Wet'
    return spei_class

def get_monitoring_ts_spei(params):
    params = _create_params_ts(params)
    data_spei = download_analysis(params)
    data_spei = json.loads(data_spei)
    if data_spei['status'] != 0: return data_spei
    data_spei['data'] = json.loads(data_spei['data'])

    if params['temporalRes'] == 'seasonal':
        params['temporalRes'] = 'monthly'

    time = format_tseries_dates(
        data_spei['data']['Dates'],
        params['temporalRes']
    )
    if time is None:
        return {
            'status': -1,
            'message': 'Unknown temporal resolution'
        }

    miss = data_spei['data']['Missing']
    values = data_spei['data']['Data'][0]['Values']
    values = np.array(values)
    values[values == miss] = np.nan

    info = {
        'geom': {
            'name': data_spei['data']['Data'][0]['Name'],
            'lon': data_spei['data']['Data'][0]['Longitude'],
            'lat': data_spei['data']['Data'][0]['Latitude']
        },
        'var':{
            'name': data_spei['data']['VariableName'],
            'units': data_spei['data']['VariableUnits'],
            'type': params['analysis']
        },
        'time_res': params['temporalRes'],
        'time_scale': params['timeScale'],
        'spei_breaks': [-2, -1.5, -1, 1, 1.5, 2],
        'spei_class': [
            'Extremely Dry', 'Severely Dry', 'Moderately Dry', 
            'Normal',
            'Moderately Wet', 'Severely Wet', 'Extremely Wet'  
        ],
        'seas_len': None,
        'seas_daily': None
    }
    out = {'time': time, 'values': values, 'info': info}
    return {'status': 0, 'data': out}

def climate_monitoring_ts_cumul(params):
    params = _create_params_ts(params)
    data_raw = download_rawdata(params)
    data_raw = json.loads(data_raw)
    if data_raw['status'] != 0: return data_raw
    data_raw['data'] = json.loads(data_raw['data'])
    time_ts = format_tseries_dates(data_raw['data']['Dates'], params['temporalRes'])
    date_ts = ['-'.join(d.split('-')[1:]) for d in time_ts]

    params_mean = _create_params_ts_clim_mean(params)
    data_mean = extract_climdata(params_mean)
    data_mean = json.loads(data_mean)
    if data_mean['status'] != 0: return data_mean
    data_mean['data'] = json.loads(data_mean['data'])
    time_clim = _format_clim_dates(data_mean['data']['Dates'])
    dek_clim = ['-'.join(d.split('-')[1:]) for d in time_clim]

    params_perc = _create_params_ts_clim_perc(params)
    data_perc = extract_climdata(params_perc)
    data_perc = json.loads(data_perc)
    if data_perc['status'] != 0: return data_perc
    data_perc['data'] = json.loads(data_perc['data'])
    # time_clim = _format_clim_dates(data_perc['data']['Dates'])

    lookup_clim = {
        d: i for i, d in enumerate(dek_clim)
    }
    it = np.array([lookup_clim[d] for d in date_ts])
    clim_m = np.array(data_mean['data']['Data'][0]['Values'])
    clim_m = np.cumsum(clim_m[it])
    clim_p = np.column_stack(data_perc['data']['Data'][0]['Values'])
    clim_p = np.cumsum(clim_p[it, :], axis=0)
    ts_d = np.array(data_raw['data']['Data'][0]['Values'])
    ts_d = np.cumsum(ts_d)

    ymin = min(
        np.nanmin(ts_d),
        np.nanmin(clim_m),
        np.nanmin(clim_p)
    )
    ymax = max(
        np.nanmax(ts_d),
        np.nanmax(clim_m),
        np.nanmax(clim_p)
    )
    breaks = pretty(ymin, ymax, 14).tolist()

    ylim = [breaks[0], breaks[-1]]
    ex = (ylim[1] - ylim[0]) * 0.01
    ylim[1] = ylim[1] + ex
    if ylim[0] < 0:
        ylim[0] = 0

    values = np.vstack(
        (ts_d, clim_m, clim_p[:, 0], clim_p[:, 1])
    )
    values = np.where(np.isnan(values), None, values)

    info = {
        'geom': {
            'name': data_mean['data']['Data'][0]['Name'],
            'lon': data_mean['data']['Data'][0]['Longitude'],
            'lat': data_mean['data']['Data'][0]['Latitude']
        },
        'var':{
            'name': 'Cumulative Rainfall',
            'units': 'mm',
            'type': params['variable']
        },
        'time_res': params['temporalRes']
    }

    data = {
        'time': time_ts,
        'values': values.tolist(),
        'info': info,
        'yrange': ylim,
        'yticks': breaks
    }
    return {'status': 0, 'data': data}

def _create_params_ts(params):
    pars_0 = {
        'gridded': False,
        'outFormat': 'JSON-Format',
        'webApp': True,
        'finalOutput': True,
        'httpMethod': 'POST',
    }
    if params['geomExtract'] == 'points':
        pars = pars_0 | {'padLon': 0, 'padLat': 0}
    else:
        pars = pars_0 | {'spatialAvg': True, 'allPolygons': False}
    return pars | params

def _create_params_ts_clim_mean(params):
    pars_0 = {
        'climFunction': 'mean',
        'fullYear': True,
        'climDate': None,
        'outFormat': 'JSON-Format',
        'gridded': False,
        'webApp': True,
        'finalOutput': True,
        'httpMethod': 'POST',
    }
    if params['geomExtract'] == 'points':
        pars = pars_0 | {'padLon': 0, 'padLat': 0}
    else:
        pars = pars_0 | {'spatialAvg': True, 'allPolygons': False}
    return pars | params

def _create_params_ts_clim_perc(params):
    pars_0 = {
        'climFunction': 'percentile',
        'precentileValue': [5.0, 95.0],
        'fullYear': True,
        'climDate': None,
        'outFormat': 'JSON-Format',
        'gridded': False,
        'webApp': True,
        'finalOutput': True,
        'httpMethod': 'POST',
    }
    if params['geomExtract'] == 'points':
        pars = pars_0 | {'padLon': 0, 'padLat': 0}
    else:
        pars = pars_0 | {'spatialAvg': True, 'allPolygons': False}
    return pars | params

def _format_clim_dates(dates_l):
    mdk = [t.split('_')[1] for t in dates_l]
    m = [t.split('-')[0] for t in mdk]
    dk = [t.split('-')[1] for t in mdk]
    dy = [
            '01' if d == '1'
            else 
            '11' if d == '2'
            else
            '21'
            for d in dk
        ]
    mdk = ['-'.join(l) for l in zip(m, dy)]
    return [f'2025-{t}' for t in mdk]
