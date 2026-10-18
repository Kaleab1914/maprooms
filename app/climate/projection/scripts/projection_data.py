
import re
from pathlib import Path

import xarray as xr

from app.scripts._global import GLOBAL_CONFIG


def get_climate_projection_dataset(params):
    config = GLOBAL_CONFIG['climate_projection']

    dataset = params['dataset']
    periods = {
        config['historical']['dataset']: 'historical',
        config['projection']['dataset']: 'projection'
    }

    if dataset not in periods:
        raise ValueError(f'Unknown projection dataset: {dataset}')

    period = periods[dataset]

    variable_key = params['variable']
    if variable_key not in config['variables']:
        raise ValueError(f'Unsupported variable: {variable_key}')

    variable = config['variables'][variable_key]
    info = config['netcdf'][variable]

    model = params['model']
    if not isinstance(model, str) or not re.fullmatch(
        r'[a-z0-9_-]+', model
    ):
        raise ValueError('Invalid model identifier.')

    path = (
        Path(config['zarr_dir'])
        / info['folder']
        / config[period]['directory']
        / model
    )

    if period == 'projection':
        scenario = params['scenario']

        if scenario not in config['scenarios']:
            raise ValueError(f'Unknown scenario: {scenario}')

        path = path / scenario

    path = path / f'{variable}.zarr'

    if not path.is_dir():
        raise ValueError(
            'The selected model/scenario has not been converted to Zarr.'
        )

    return xr.open_zarr(
        str(path),
        chunks=config['chunks'],
        consolidated=False
    )


def get_climate_projection_variable(dataset, params):
    config = GLOBAL_CONFIG['climate_projection']
    variable_key = params['variable']
    variable = config['variables'][variable_key]
    info = config['netcdf'][variable]

    data = dataset[info['varid']]
    attrs = dict(data.attrs)
    units = attrs.get('units', '').strip()

    if variable_key in (
        'maximum_temperature',
        'minimum_temperature'
    ):
        if units == 'K':
            data = data - 273.15
        elif units not in ('°C', 'degC', 'degrees_Celsius'):
            raise ValueError(f'Unsupported temperature units: {units}')

        attrs['units'] = '°C'

    elif variable_key == 'rainfall':
        # Daily precipitation expressed as a mean rate.
        if units in ('kg m-2 s-1', 'kg m^-2 s^-1'):
            data = data * 86400.0
        elif units not in ('mm/day', 'mm day-1', 'mm d-1', 'mm'):
            raise ValueError(f'Unsupported precipitation units: {units}')

        attrs['units'] = 'mm/day'

    else:
        raise ValueError(f'Unknown projection variable: {variable_key}')

    data.attrs = attrs
    return data


