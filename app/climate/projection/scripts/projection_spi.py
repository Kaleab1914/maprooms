
import re

import numpy as np
import xarray as xr

from contextlib import ExitStack

from app.scripts._global import GLOBAL_CONFIG
from app.scripts.imagepng import create_imagePng

from .projection_data import (
    get_climate_projection_dataset,
    get_climate_projection_variable,
)
from .projection_sp import _integer


from calendar import monthrange

from app.dst_api.scripts.spei_functions import (
    SPEI_Aggregate_data,
    SPEI_Compute_params,
    SPEI_Computation_ts,
)

from app.scripts.colorbar import check_invalid_colors

from pathlib import Path

from app.scripts.util import load_yaml_file

from app.dst_api.scripts.shapefiles import get_shapefiles_data

from app.dst_api.scripts.extract import (
    create_geom_polygons,
    json_coords_polygons,
)

REFERENCE_START_YEAR = 1981
REFERENCE_END_YEAR = 2014


def _dataset_params(params):
    config = GLOBAL_CONFIG['climate_projection']

    if params['scenario'] not in config['scenarios']:
        raise ValueError('Unknown projection scenario.')

    return {
        **params,
        'variable': 'rainfall',
        'dataset': config['projection']['dataset'],
    }


def _reference_parameters(params):
    # Fixed here, maybe later change it based on the user requirement, but is that make sens?
    return REFERENCE_START_YEAR, REFERENCE_END_YEAR, 30


def _accumulation_length(params):
    return _integer(params, 'timeScale', 2, 12)


def _month_number(value):
    year, month = map(int, value.split('-'))
    return year * 12 + month - 1


def _month_text(number):
    year, month = divmod(number, 12)
    return f'{year:04d}-{month + 1:02d}'


def _shift_month(value, offset):
    return _month_text(_month_number(value) + offset)


def _chart_month_bounds(params):
    start = _integer(params, 'plotStartYear', 1981, 2100)
    end = _integer(params, 'plotEndYear', 1981, 2100)

    if start > end:
        raise ValueError('Chart start year exceeds the end year.')

    return f'{start:04d}-01', f'{end:04d}-12'

def _distribution(params):
    distribution = params.get('distribution', 'gamma')

    if distribution not in ('gamma', 'peasron3'):
        raise ValueError('Unsupported SPI distribution.')

    return distribution


def _rainfall(dataset, params):
    data = get_climate_projection_variable(dataset, params)

    return data.assign_coords(
        lon=((data.lon + 180) % 360) - 180
    ).sortby('lon').sortby('lat')


def _monthly_totals(data):
    if data.sizes['time'] == 0:
        raise ValueError('No rainfall data within the selected period.')

    dates = data.time.dt.strftime('%Y-%m-%d').values

    if (
        np.unique(dates).size != dates.size
        or not data.indexes['time'].is_monotonic_increasing
    ):
        raise ValueError(
            'Expected unique, increasing daily observations.'
        )

    data = data.where(np.isfinite(data) & (data >= 0))

    monthly = data.resample(time='MS').sum(skipna=False)
    counts = data.resample(time='MS').count()

    monthly = monthly.where(
        counts == monthly.time.dt.days_in_month
    )


    labels = np.asarray(
        monthly.time.dt.strftime('%Y-%m-01').values,
        dtype='datetime64[ns]',
    )

    monthly = monthly.assign_coords(time=labels)
    monthly.attrs['units'] = 'mm'

    return monthly.transpose('time', 'lat', 'lon')


def _spi_month_parameter(params, key):
    value = params.get(key)

    if (
        not isinstance(value, str)
        or re.fullmatch(
            r'\d{4}-(0[1-9]|1[0-2])',
            value,
        ) is None
        or int(value[:4]) < 1
    ):
        raise ValueError(f'Invalid month parameter: {key}')

    return value


def _pad_spi_calendar_to_january(monthly):

    first_month = int(
        monthly.time.dt.month.isel(time=0).item()
    )

    if first_month == 1:
        return monthly

    first_time = monthly.time.values[0]

    if isinstance(monthly.indexes['time'], xr.CFTimeIndex):
        january = first_time.replace(month=1, day=1)
    else:
        first_year = int(
            monthly.time.dt.year.isel(time=0).item()
        )
        january = np.datetime64(
            f'{first_year:04d}-01-01'
        )

    padding = xr.full_like(
        monthly.isel(time=[0]),
        np.nan,
        dtype=float,
    ).assign_coords(time=[january])

    return xr.concat(
        [padding, monthly],
        dim='time',
    ).resample(time='MS').asfreq()


def _compute_projection_spi(
    historical_monthly,
    evaluation_monthly,
    distribution='gamma',
    month=None,
    base_start=REFERENCE_START_YEAR,
    base_end=REFERENCE_END_YEAR,
    min_years=30,
):


    historical_monthly = historical_monthly.transpose(
        'time', 'lat', 'lon'
    )

    evaluation_monthly = evaluation_monthly.transpose(
        'time', 'lat', 'lon'
    )

    reference = historical_monthly.sel(
        time=slice(
            f'{base_start:04d}-01',
            f'{base_end:04d}-12',
        )
    )

    actual = (
        reference.time.dt.year.values * 12
        + reference.time.dt.month.values - 1
    )

    expected = np.arange(
        base_start * 12,
        (base_end + 1) * 12,
    )

    if not np.array_equal(actual, expected):
        raise ValueError(
            f'Historical data must cover January {base_start} '
            f'through December {base_end}.'
        )


    if evaluation_monthly.sizes['time'] == 0:
        raise ValueError(
            'No observations within the selected display period.'
        )

    reference, evaluation_monthly = xr.align(
        reference,
        evaluation_monthly,
        join='exact',
        exclude={'time'},
    )

    if month is not None:
        if month not in range(1, 13):
            raise ValueError('Invalid SPI calendar month.')

        reference = reference.where(
            reference.time.dt.month == month
        )

    original_time = evaluation_monthly.time

    reference = reference.compute()

    valid_years = reference.notnull().groupby(
        'time.month'
    ).sum('time')

    sufficient = valid_years.sel(
        month=reference.time.dt.month
    ).transpose('time', 'lat', 'lon')

    reference = reference.where(
        sufficient.values >= min_years
    )
    evaluation = _pad_spi_calendar_to_january(
        evaluation_monthly
    ).compute()

    fitted = SPEI_Compute_params(
        reference,
        tscale=1,
        frequency=12,
        distribution=distribution,
        min_non_na=5,
        n_jobs=1,
    )

    reference_length = reference.sizes['time']
    evaluation_length = evaluation.sizes['time']


    context = xr.concat(
        [
            reference.assign_coords(
                time=np.arange(reference_length)
            ),
            evaluation.assign_coords(
                time=np.arange(
                    reference_length,
                    reference_length + evaluation_length,
                )
            ),
        ],
        dim='time',
    )

    evaluated = SPEI_Computation_ts(
        context,
        fitted,
        tscale=1,
        frequency=12,
        distribution=distribution,
        time_res='monthly',
        spei_type='spi',
    )

    spi = evaluated.isel(
        time=slice(reference_length, None)
    ).assign_coords(time=evaluation.time)

    spi = spi.sel(time=original_time)


    wet = (reference > 0).where(reference.notnull())

    wet_fraction = wet.groupby('time.month').mean(
        'time',
        skipna=True,
    )

    eligible = wet_fraction.sel(
        month=spi.time.dt.month
    ) > (1.0 / 3.0)

    spi = spi.where(eligible)

    spi.attrs.update({
        'reference_start_year': base_start,
        'reference_end_year': base_end,
        'minimum_reference_years': min_years,
        'reference_source': 'same_model_historical',
    })


    return spi



def _read_projection_spi(
    params,
    start_date,
    end_date,
    point=None,
    month=None,
    polygon=None,
):
    config = GLOBAL_CONFIG['climate_projection']
    length = _accumulation_length(params)
    base_start, base_end, min_years = _reference_parameters(params)

    future_params = _dataset_params(params)

    historical_params = {
        **future_params,
        'dataset': config['historical']['dataset'],
    }

    with (
        get_climate_projection_dataset(
            historical_params
        ) as historical_ds,
        get_climate_projection_dataset(
            future_params
        ) as future_ds,
    ):
        historical = _rainfall(
            historical_ds, historical_params
        )
        future = _rainfall(
            future_ds, future_params
        )

        historical, future = xr.align(
            historical,
            future,
            join='exact',
            exclude={'time'},
        )

        region_mask = None

        if polygon is not None:
            historical, future, region_mask = (
                _subset_projection_spi_polygon(
                    historical,
                    future,
                    polygon,
                )
            )

        if point is not None:
            lon, lat = point

            if not (
                float(historical.lon.min())
                <= lon
                <= float(historical.lon.max())
                and float(historical.lat.min())
                <= lat
                <= float(historical.lat.max())
            ):
                raise ValueError(
                    'Selected point is outside model coverage.'
                )

            historical = historical.sel(
                lon=[lon],
                lat=[lat],
                method='nearest',
            )

            future = future.sel(
                lon=historical.lon,
                lat=historical.lat,
            )

        historical = historical.sel(
            time=slice('1980-01', '2014-12')
        )

        pieces = [_monthly_totals(historical)]

        if end_date >= '2015-01':

            future_start = max(
                '2015-01',
                _shift_month(start_date, 1 - length),
            )

            selected_future = future.sel(
                time=slice(future_start, end_date)
            )

            pieces.append(_monthly_totals(selected_future))

        monthly = xr.concat(pieces, dim='time').sortby('time')

        if region_mask is not None:
            # average montlhy before calcul of SPI, need to check this later as well
            monthly = (
                monthly.where(region_mask)
                .mean(
                    dim=('lat', 'lon'),
                    skipna=True,
                )
                .expand_dims(
                    lat=[polygon['lat']],
                    lon=[polygon['lon']],
                )
                .transpose('time', 'lat', 'lon')
            )
        last_month = max('2014-12', end_date)

        full_time = np.arange(
            np.datetime64('1980-01'),
            np.datetime64(_shift_month(last_month, 1)),
            dtype='datetime64[M]',
        ).astype('datetime64[ns]')

        monthly = monthly.reindex(
            time=full_time
        ).transpose('time', 'lat', 'lon').compute()

        accumulated = SPEI_Aggregate_data(
            monthly,
            tscale=length,
        )

        complete = (
            monthly.notnull()
            .rolling(time=length, min_periods=length)
            .sum()
            == length
        )

        accumulated = accumulated.where(complete)

        reference = accumulated.sel(
            time=slice(
                f'{base_start}-01',
                f'{base_end}-12',
            )
        )

        evaluation = accumulated.sel(
            time=slice(start_date, end_date)
        )

        spi = _compute_projection_spi(
            reference,
            evaluation,
            distribution=_distribution(params),
            month=month,
            base_start=base_start,
            base_end=base_end,
            min_years=min_years,
        )

        spi.attrs['time_scale'] = length
        if polygon is not None:
            spi.attrs['geometry_type'] = 'polygon'
            spi.attrs['geometry_name'] = str(polygon['name'])
            spi.attrs['grid_cell_count'] = int(
                region_mask.sum().item()
            )
            
            spi.attrs['spatial_method'] = polygon.get(
                'spatial_method',
                'polygon_mean',
            )

            spi.attrs['selection_warning'] = polygon.get(
                'selection_warning'
            )
            
    return spi



def get_climate_projection_spi_sp_data(params):
    base_start, base_end, min_years = _reference_parameters(params)
    length = _accumulation_length(params)
    start_month = _spi_month_parameter(params, 'mapMonth')

    if not '2015-01' <= start_month <= '2100-12':
        raise ValueError(
            'Select a projection start month between 2015 and 2100.'
        )

    end_month = _shift_month(start_month, length - 1)

    if end_month > '2100-12':
        raise ValueError(
            'The accumulation window extends beyond 2100.'
        )

    colorbar = params.get('colorbar')

    if colorbar is not None:
        check = check_invalid_colors(colorbar)

        if check['status'] == -1:
            raise ValueError(check['message'])

    spi = _read_projection_spi(
        params,
        start_date=end_month,
        end_date=end_month,
        month=int(end_month[5:7]),
    )

    if spi.sizes['time'] != 1:
        raise ValueError(
            'The selected accumulation window is outside coverage.'
        )

    field = spi.isel(
        time=0, drop=True
    ).transpose('lat', 'lon')

    if not np.isfinite(field.values).any():
        raise ValueError(
            'No valid SPI values for this accumulation window '
            'using the historical reference.'
        )

    return {
        'status': 0,
        'lon': field.lon.values,
        'lat': field.lat.values,
        'data': field.values,
        'varid': 'spi',
        'longname': (
            f'Standardized Precipitation Index (SPI-{length})'
        ),
        'units': '',
        'date': (
            f"{start_month}–{end_month}: "
            f"{params['model']} — {params['scenario']}; "
            f"reference {base_start}–{base_end}"
        ),
        'distribution': _distribution(params),
        'time_scale': length,
        'baseline_period': [base_start, base_end],
        'minimum_reference_years': min_years,
        'colorbar': colorbar,
    }



def climate_projection_spi_sp_data(data):
    colorbar = data.get('colorbar')

    color_args = {
        'breaks': [-2, -1.5, -1, 1, 1.5, 2],
        'color_name': 'spi_colors',
    }

    if colorbar is not None:
        color_args = {
            'breaks': (
                colorbar['break_cbar']
                if colorbar['break_cbar'] is not None
                else [-2, -1.5, -1, 1, 1.5, 2]
            ),
            'colors_ext': colorbar['color_ext'],
        }

        if colorbar['color_type'] == 'preset':
            color_args['color_name'] = colorbar['color_cbar']
        else:
            color_args['colors'] = colorbar['color_cbar']

    result = create_imagePng(data, **color_args)

    if result is None:
        raise ValueError('Unable to render the SPI map.')

    result['date'] = data['date']
    result['ckeys']['title'] = data['longname']

    for key in (
        'distribution',
        'time_scale',
        'baseline_period',
        'minimum_reference_years',
    ):
        result[key] = data[key]

    return {'status': 0, 'data': result}



def climate_projection_spi_ts_data(params):
    base_start, base_end, min_years = _reference_parameters(params)
    start_date, end_date = _chart_month_bounds(params)
    length = _accumulation_length(params)

    mode = params.get('geomExtract', 'points')
    point = None
    polygon = None

    if mode == 'points':
        points = params.get('pointsList')

        if (
            not isinstance(points, list)
            or len(points) != 1
            or not isinstance(points[0], dict)
        ):
            raise ValueError('Select one map point.')

        lon = float(points[0]['lon'])
        lat = float(points[0]['lat'])

        if not np.isfinite([lon, lat]).all():
            raise ValueError('Invalid point coordinates.')

        point = ((lon + 180) % 360 - 180, lat)

    elif mode == 'polygons':
        polygon = _projection_spi_polygon(params)

    else:
        raise ValueError('Unsupported spatial selection.')

    spi = _read_projection_spi(
        params,
        start_date=start_date,
        end_date=end_date,
        point=point,
        polygon=polygon,
    )

    grid_lon = float(spi.lon.values[0])
    grid_lat = float(spi.lat.values[0])

    series = spi.isel(lat=0, lon=0)

    if series.sizes['time'] == 0:
        raise ValueError(
            'No data within the selected chart period.'
        )

    values = np.asarray(series.values, dtype=float)
    finite = np.isfinite(values)

    if not finite.any():
        raise ValueError(
            'No valid SPI values at this point using '
            'the selected historical reference.'
        )

    limit = max(
        3,
        int(np.ceil(np.max(np.abs(values[finite])))),
    )

    return {
        'status': 0,
        'data': {
            'time': series.time.dt.strftime(
                '%Y-%m-01'
            ).values.tolist(),
            'values': [
                float(value) if np.isfinite(value) else None
                for value in values
            ],
            'yrange': [-limit, limit],
            'yticks': list(range(-limit, limit + 1)),
            'info': {
                'var': {
                    'name': f'SPI-{length}',
                    'units': '',
                    'type': 'spi',
                },
                'time_res': 'monthly',
                'time_scale': length,
                'seas_len': None,
                'seas_daily': None,
                'historical_period': [1981, 2014],
                'month_convention': 'accumulation_ending_month',
                'model': params['model'],
                'scenario': params['scenario'],
                'distribution': _distribution(params),
                'reference': 'same_model_historical',
                'baseline_period': [base_start, base_end],
                'minimum_reference_years': min_years,

                'calculation_engine': (
                    'SPEI_Compute_params + SPEI_Computation_ts'
                ),
                'spei_breaks': [-2, -1.5, -1, 1, 1.5, 2],
                'spei_class': [
                    'Extremely Dry',
                    'Severely Dry',
                    'Moderately Dry',
                    'Near Normal',
                    'Moderately Wet',
                    'Severely Wet',
                    'Extremely Wet',
                ],

                'geom': {
                    'type': spi.attrs.get('geometry_type', 'point'),
                    'name': spi.attrs.get('geometry_name', 'Point'),
                    'lon': grid_lon,
                    'lat': grid_lat,
                    'grid_cell_count': spi.attrs.get('grid_cell_count', 1),
                },
            },
        },
    }



def climate_projection_spi_coverage_data(params):
    selected_params = _dataset_params(params)
    length = _accumulation_length(params)

    with get_climate_projection_dataset(
        selected_params
    ) as dataset:
        data = get_climate_projection_variable(
            dataset, selected_params
        )

        lon = np.sort(((np.asarray(data.lon.values) + 180) % 360) - 180)
        lat = np.sort(np.asarray(data.lat.values))

        if lon.size < 2 or lat.size < 2:
            raise ValueError('Insufficient model grid coordinates.')

        spatial_resolution = {
            'lon': float(np.round(np.median(np.diff(lon)), 6)),
            'lat': float(np.round(np.median(np.diff(lat)), 6)),
        }

        if data.sizes['time'] == 0:
            raise ValueError('The selected dataset has no data.')

        dates = data.time.isel(time=[0, -1])

        years = dates.dt.year.values
        months = dates.dt.month.values
        days = dates.dt.day.values
        month_lengths = dates.dt.days_in_month.values

        first = (
            int(years[0]) * 12 + int(months[0]) - 1
            + int(days[0] > 1)
        )

        last = (
            int(years[-1]) * 12 + int(months[-1]) - 1
            - int(days[-1] < month_lengths[-1])
        )

    first = max(first, _month_number('2015-01'))
    last = min(last, _month_number('2100-12'))

    last_start = last - length + 1

    if first > last_start:
        raise ValueError(
            'No complete accumulation window is available.'
        )

    start_text = _month_text(first)
    end_text = _month_text(last_start)
    end_year, end_month = map(int, end_text.split('-'))

    return {
        'status': 0,
        'data': {
            'start': f'{start_text}-01',
            'end': (
                f'{end_text}-'
                f'{monthrange(end_year, end_month)[1]:02d}'
            ),
            'plot_start_year': REFERENCE_START_YEAR,
            'plot_end_year': last // 12,
            'spatial_resolution': spatial_resolution,
        },
    }




def _projection_spi_polygon(params):
    name = params.get('Poly')

    if name is None or name == '' or isinstance(name, list):
        raise ValueError('Select one region or zone.')

    config_path = (
        Path(GLOBAL_CONFIG['app_dir'])
        / 'yaml'
        / 'subdivision-config.yaml'
    )

    subdivisions = load_yaml_file(str(config_path))['subdivision']

    configured = any(
        layer.get('file') == params.get('shpFile')
        and layer.get('field') == params.get('shpField')
        for layer in subdivisions.values()
    )

    if not configured:
        raise ValueError('Unknown spatial-selection layer.')

    selection = get_shapefiles_data({
        **params,
        'shpSource': 'default',
        'allPolygons': False,
    })

    if selection['status'] != 0:
        raise ValueError(selection['message'])

    shapefile = selection['shp']
    field = params['shpField']

    selected = shapefile[shapefile[field] == name]

    if selected.empty:
        raise ValueError('The selected region was not found.')

    coordinates = json_coords_polygons(
        shapefile,
        field,
        [name],
    )[0]

    return {
        'shp': shapefile,
        'field': field,
        'name': name,
        'lon': coordinates['Longitude'],
        'lat': coordinates['Latitude'],
    }


def _subset_projection_spi_polygon(historical, future, polygon):
    rows, columns = create_geom_polygons(
        {
            'lon': historical.lon.values,
            'lat': historical.lat.values,
        },
        polygon['shp'],
        polygon['field'],
        polygon['name'],
    )

    if rows.size == 0:
        lon = float(polygon['lon'])
        lat = float(polygon['lat'])

        if not (
            float(historical.lon.min())
            <= lon
            <= float(historical.lon.max())
            and float(historical.lat.min())
            <= lat
            <= float(historical.lat.max())
        ):
            raise ValueError(
                'The selected region is outside model coverage.'
            )

        # Reuse the existing point-selection approach.
        historical = historical.sel(
            lon=[lon],
            lat=[lat],
            method='nearest',
        )

        future = future.sel(
            lon=historical.lon,
            lat=historical.lat,
        )

        polygon['lon'] = float(historical.lon.values[0])
        polygon['lat'] = float(historical.lat.values[0])

        polygon['spatial_method'] = 'representative_gridpoint'
        polygon['selection_warning'] = (
            f"{polygon['name']}: displaying a representative "
            "model grid cell because the polygon contains "
            "no model grid-cell centres."
        )

        mask = xr.DataArray(
            [[True]],
            dims=('lat', 'lon'),
            coords={
                'lat': historical.lat,
                'lon': historical.lon,
            },
        )

        return historical, future, mask


    y0 = int(rows.min())
    y1 = int(rows.max()) + 1
    x0 = int(columns.min())
    x1 = int(columns.max()) + 1

    historical = historical.isel(
        lat=slice(y0, y1),
        lon=slice(x0, x1),
    )

    future = future.isel(
        lat=slice(y0, y1),
        lon=slice(x0, x1),
    )

    values = np.zeros(
        (y1 - y0, x1 - x0),
        dtype=bool,
    )

    values[rows - y0, columns - x0] = True

    mask = xr.DataArray(
        values,
        dims=('lat', 'lon'),
        coords={
            'lat': historical.lat,
            'lon': historical.lon,
        },
    )

    return historical, future, mask

