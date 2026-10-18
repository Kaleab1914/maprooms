
import calendar

import numpy as np
import xarray as xr

from app.scripts._global import GLOBAL_CONFIG
from app.scripts.colorbar import check_invalid_colors
from app.scripts.imagepng import create_imagePng

from .projection_data import (
    get_climate_projection_dataset,
    get_climate_projection_variable
)


def _integer(params, key, minimum, maximum):
    value = params[key]
    number = int(value)

    if float(value) != number or not minimum <= number <= maximum:
        raise ValueError(f'Invalid parameter: {key}')

    return number


def climate_projection_sp_data(params):
    colorbar = params['colorbar']

    check = check_invalid_colors(colorbar)
    if check['status'] == -1:
        return check

    data = get_climate_projection_sp_data(params)

    if not np.isfinite(data['data']).any():
        return {
            'status': -1,
            'message': 'No complete seasonal data for these selections.'
        }

    breaks = colorbar['break_cbar']

    # if breaks is None:
    #     limit = 10 if params['variable'] == 'rainfall' else 3
    #     breaks = np.arange(-limit, limit + 0.5).tolist()

    if breaks is None:
        if params['variable'] == 'rainfall':
            breaks = np.arange(-3, 4, 1).tolist()
        else:
            breaks = np.arange(-4, 4.5, 0.5).tolist()

    color_args = {
        'breaks': breaks,
        'colors_ext': (
            list(colorbar['color_ext'])
            if colorbar['color_ext'] is not None else None
        )
    }

    if colorbar['color_type'] == 'preset':
        color_args['color_name'] = colorbar['color_cbar']
    else:
        color_args['colors'] = colorbar['color_cbar']

    result = create_imagePng(data, **color_args)

    if result is None:
        return {
            'status': -1,
            'message': 'Unable to render the seasonal change map.'
        }

    result['date'] = data['date']
    result['ckeys']['title'] = (
        f"{data['longname']} ({data['units']})"
    )

    return {'status': 0, 'data': result}


def get_climate_projection_sp_data(params):
    start_month = _integer(params, 'seasStart', 1, 12)
    end_month = _integer(params, 'seasEnd', 1, 12)
    # historical_year = _integer(params, 'yearstartH', 1, 9998)

    historical_year = 1981
    historical_end = 2014

    historical_period = (historical_end - historical_year + 1 - int(end_month < start_month))
    future_year = _integer(params, 'yearstartFut', 1, 9998)
    period = _integer(params, 'climPeriod', 1, 9998)

    if max(historical_year, future_year) + period > 9999:
        raise ValueError('Selected period exceeds the supported year range.')

    config = GLOBAL_CONFIG['climate_projection']

    historical_params = {
        **params,
        'dataset': config['historical']['dataset']
    }
    future_params = {
        **params,
        'dataset': config['projection']['dataset']
    }

    with (
        get_climate_projection_dataset(historical_params) as historical_ds,
        get_climate_projection_dataset(future_params) as future_ds
    ):
        historical = get_climate_projection_variable(
            historical_ds, historical_params
        )
        future = get_climate_projection_variable(
            future_ds, future_params
        )

        if historical.attrs['units'] != future.attrs['units']:
            raise ValueError('Historical and future units do not match.')

        units = historical.attrs['units']

        historical_clim = _seasonal_climatology(
            historical,
            historical_year,
            historical_period,
            start_month,
            end_month
        )

        future_clim = _seasonal_climatology(
            future,
            future_year,
            period,
            start_month,
            end_month
        )

        historical_clim, future_clim = xr.align(
            historical_clim,
            future_clim,
            join='exact'
        )

        change = (
            future_clim - historical_clim
        ).transpose('lat', 'lon').compute()

    variable = config['variables'][params['variable']]
    variable_name = config['netcdf'][variable]['name']

    season = (
        f'{calendar.month_abbr[start_month]}–'
        f'{calendar.month_abbr[end_month]}'
    )

    return {
        'status': 0,
        'lon': change.lon.values,
        'lat': change.lat.values,
        'data': change.values,
        'varid': 'clim_var',
        'longname': f'Seasonal change: {variable_name}',
        'units': units,
        'date': (
            f'{season}: '
            f'{future_year}–{future_year + period - 1} minus '
            f'{historical_year}–{historical_end}'
        )
    }

def _seasonal_values(data, year, period, start, end, rainfall=False ):
    length = (end - start) % 12 + 1
    crosses_year = int(end < start)
    final_year = year + period - 1 + crosses_year

    data = data.assign_coords(
        lon=((data.lon + 180) % 360) - 180
    ).sortby('lon').sortby('lat')

    data = data.sel(
        time=slice(
            f'{year:04d}-{start:02d}',
            f'{final_year:04d}-{end:02d}'
        )
    )

    if (
        data.sizes['time'] == 0
        or data.sizes['lat'] < 1
        or data.sizes['lon'] < 1
    ):
        raise ValueError('Insufficient temporal or geographic coverage.')

    dates = data.time.dt.strftime('%Y-%m-%d').values

    if (
        np.unique(dates).size != dates.size
        or not data.indexes['time'].is_monotonic_increasing
    ):
        raise ValueError('Expected unique, increasing daily observations.')


    if rainfall:
        monthly = data.resample(time='MS').sum(skipna=False)
    else:
        monthly = data.resample(time='MS').mean(skipna=False)

    counts = data.resample(time='MS').count()

    monthly = monthly.where(
        counts == monthly.time.dt.days_in_month
    )

    seasons = []

    for season_year in range(year, year + period):
        selected = monthly.sel(
            time=slice(
                f'{season_year:04d}-{start:02d}',
                f'{season_year + crosses_year:04d}-{end:02d}'
            )
        )

        actual = (
            selected.time.dt.year.values * 12
            + selected.time.dt.month.values - 1
        )
        expected = (
            season_year * 12 + start - 1 + np.arange(length)
        )

        if not np.array_equal(actual, expected):
            raise ValueError(
                f'Incomplete coverage for the season starting '
                f'in {season_year}.'
            )
            

        if rainfall:
            seasonal = selected.sum('time', skipna=False)
        else:
            seasonal = selected.mean('time', skipna=False)

        seasons.append(
            seasonal.expand_dims(season_year=[season_year])
        )

    # return xr.concat(seasons, dim='season_year').mean(
    #     'season_year', skipna=False
    # )
    return xr.concat(seasons, dim='season_year')

def _seasonal_climatology(data, year, period, start, end):
    return _seasonal_values(
        data, year, period, start, end
    ).mean('season_year', skipna=False)

