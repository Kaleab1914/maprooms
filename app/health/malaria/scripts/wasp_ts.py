
from pathlib import Path

import numpy as np
import xarray as xr
import pandas as pd
import hashlib
import json

from threading import Lock

from app.scripts._cache import cache

from .wasp_data import (
    CACHE_VERSION as WASP_CALIBRATION_CACHE_VERSION,
)


from app.scripts._global import GLOBAL_CONFIG
from app.scripts.util import load_yaml_file

from app.dst_api.scripts.shapefiles import (
    get_shapefiles_data,
)

from app.dst_api.scripts.extract import (
    create_geom_polygons,
    create_geom_polygons_select,
)

from .wasp import (
    _integer,
    _arguments,
    WASP_Computation_ts,
)

from .wasp_data import (
    get_wasp_xr_data,
    get_wasp_parameters,
)

from .wasp import WASP_Computation_ts
from .wasp_data import get_wasp_parameters

WASP_SERIES_CACHE_VERSION = "health-wasp-series-v1"
WASP_SERIES_LOCK = Lock()

def _spatial_selection(precip, fitted, params):

    if params.get("countryAverage") is True:
        config_path = (
            Path(GLOBAL_CONFIG["app_dir"])
            / "yaml"
            / "subdivision-config.yaml"
        )

        layers = load_yaml_file(
            str(config_path)
        )["subdivision"]

        region = layers.get("region")

        if region is None:
            raise ValueError(
                "A complete Region layer is required "
                "for the country average."
            )

        polygons = get_shapefiles_data({
            "shpSource": "default",
            "shpFile": region["file"],
            "shpField": region["field"],
            "Poly": [],
            "allPolygons": True,
        })

        if polygons["status"] != 0:
            raise ValueError(polygons["message"])

        country = (
            polygons["shp"]
            .to_crs("EPSG:4326")
            .dissolve()
        )

        rows, columns = create_geom_polygons_select(
            {
                "lon": precip.lon.values,
                "lat": precip.lat.values,
            },
            country,
        )

        if rows.size == 0:
            raise ValueError(
                "No rainfall grid-cell centres fall "
                "inside the country boundary."
            )

        indexers = {
            "lat": xr.DataArray(rows, dims="cell"),
            "lon": xr.DataArray(columns, dims="cell"),
        }

        return (
            precip.isel(**indexers),
            fitted.isel(**indexers)
            if fitted is not None else None,
            {
                "type": "polygon",
                "name": "Whole country",
                "grid_cell_count": int(rows.size),
                "spatial_method": (
                    "grid_centres_cosine_latitude_weighted"
                ),
            },
        )



    geometry = params.get("geomExtract", "points")

    if geometry == "points":
        points = params.get("pointsList")

        if not isinstance(points, list) or not points:
            raise ValueError("Select a point on the map.")

        point = points[0]

        lon = float(point["lon"])
        lat = float(point["lat"])

        if not np.isfinite([lon, lat]).all():
            raise ValueError(
                "Invalid point coordinates."
            )

        if not (
            float(precip.lon.min()) <= lon <= float(precip.lon.max())
            and float(precip.lat.min()) <= lat <= float(precip.lat.max())
        ):
            raise ValueError(
                "The selected point is outside rainfall coverage."
            )

        selected = precip.sel(
            lon=lon,
            lat=lat,
            method="nearest",
        )

        selected_parameters = (
            fitted.sel(
                lon=selected.lon,
                lat=selected.lat,
            )
            if fitted is not None
            else None
        )

        return selected, selected_parameters, {
            "type": "point",
            "name": point.get("loc", "Point"),
            "lon": float(selected.lon),
            "lat": float(selected.lat),
            "grid_cell_count": 1,
        }

    if geometry != "polygons":
        raise ValueError(
            "Unsupported spatial selection."
        )

    name = params.get("Poly")

    if not isinstance(name, str) or not name:
        raise ValueError(
            "Select one administrative polygon."
        )

    config_path = (
        Path(GLOBAL_CONFIG["app_dir"])
        / "yaml"
        / "subdivision-config.yaml"
    )

    layers = load_yaml_file(
        str(config_path)
    )["subdivision"]

    configured = any(
        layer.get("file") == params.get("shpFile")
        and layer.get("field") == params.get("shpField")
        for layer in layers.values()
    )

    if not configured:
        raise ValueError(
            "Unknown administrative layer."
        )

    polygons = get_shapefiles_data({
        **params,
        "shpSource": "default",
        "allPolygons": False,
    })

    if polygons["status"] != 0:
        raise ValueError(
            polygons["message"]
        )

    rows, columns = create_geom_polygons(
        {
            "lon": precip.lon.values,
            "lat": precip.lat.values,
        },
        polygons["shp"],
        params["shpField"],
        name,
    )

    if rows.size == 0:
        raise ValueError(
            "No rainfall grid-cell centres fall inside "
            "the selected polygon."
        )

    indexers = {
        "lat": xr.DataArray(rows, dims="cell"),
        "lon": xr.DataArray(columns, dims="cell"),
    }

    return (
        precip.isel(**indexers),
        fitted.isel(**indexers) if fitted is not None else None,
        {
            "type": "polygon",
            "name": name,
            "grid_cell_count": int(rows.size),
            "spatial_method": (
                "grid_centres_cosine_latitude_weighted"
            ),
        },
    )


def health_wasp_ts_data(params, precip=None):
    arguments = _arguments(params)
    length = arguments["tscale"]

    if precip is None:
        precip = get_wasp_xr_data(params)

    first_year = int(precip.time.dt.year.values[0])
    last_year = int(precip.time.dt.year.values[-1])

    chart_params = {
        **params,
        "plotStartYear": params.get(
            "plotStartYear", first_year
        ),
        "plotEndYear": params.get(
            "plotEndYear", last_year
        ),
    }

    plot_start = _integer(
        chart_params, "plotStartYear", 1, 9998
    )
    plot_end = _integer(
        chart_params, "plotEndYear", 1, 9998
    )

    if plot_start > plot_end:
        raise ValueError(
            "Chart start year exceeds the end year."
        )

    display_start = pd.Timestamp(
        year=plot_start, month=1, day=1
    )
    display_end = pd.Timestamp(
        year=plot_end, month=12, day=1
    )

    fitted = get_wasp_parameters(precip, params)

    calculation_start = display_start - pd.DateOffset(
        months=length - 1
    )

    rainfall_window = precip.sel(
        time=slice(calculation_start, display_end)
    )

    if rainfall_window.sizes["time"] == 0:
        raise ValueError(
            "No rainfall within the selected chart period."
        )

    selected, selected_parameters, geometry = (
        _spatial_selection(
            rainfall_window,
            fitted,
            params,
        )
    )

    if "cell" not in selected.dims:
        # Point: load the selected rainfall before doing arithmetic ????
        rainfall = selected.compute(
            scheduler="single-threaded"
        )

        wasp = WASP_Computation_ts(
            rainfall,
            selected_parameters,
            tscale=length,
        )

    else:
        # Country/polygon: calculate WASP per cell in bounded batches,
        # then combine the weighted sums into one spatial mean ????
        number_of_months = selected.sizes["time"]
        number_of_cells = selected.sizes["cell"]

        weighted_total = np.zeros(
            number_of_months, dtype=float
        )
        valid_weight_total = np.zeros(
            number_of_months, dtype=float
        )

        batch_size = 1000

        for offset in range(
            0, number_of_cells, batch_size
        ):
            cells = slice(offset, offset + batch_size)

            rainfall = selected.isel(
                cell=cells
            ).compute(scheduler="single-threaded")

            parameters = selected_parameters.isel(
                cell=cells
            )

            batch_wasp = WASP_Computation_ts(
                rainfall,
                parameters,
                tscale=length,
            ).transpose("time", "cell")

            batch_values = np.asarray(
                batch_wasp.values,
                dtype=float,
            )

            weights = np.cos(
                np.deg2rad(rainfall.lat.values)
            )

            valid = np.isfinite(batch_values)

            weighted_total += np.sum(
                np.where(valid, batch_values, 0.0)
                * weights[None, :],
                axis=1,
            )

            valid_weight_total += np.sum(
                valid * weights[None, :],
                axis=1,
            )

        average = np.divide(
            weighted_total,
            valid_weight_total,
            out=np.full(number_of_months, np.nan),
            where=valid_weight_total > 0,
        )

        wasp = xr.DataArray(
            average,
            dims="time",
            coords={"time": selected.time},
            name="wasp",
        )

    series = wasp.sel(
        time=slice(display_start, display_end)
    )

    values = np.asarray(series.values, dtype=float)
    finite = values[np.isfinite(values)]

    if finite.size == 0:
        raise ValueError(
            "No valid WASP values for this selection."
        )

    limit = max(
        3,
        int(np.ceil(np.max(np.abs(finite)))),
    )

    return {
        "status": 0,
        "data": {
            "time": series.time.dt.strftime(
                "%Y-%m-01"
            ).values.tolist(),
            "values": [
                float(value)
                if np.isfinite(value)
                else None
                for value in values
            ],
            "yrange": [-limit, limit],
            "yticks": list(range(-limit, limit + 1)),
            "info": {
                "var": {
                    "name": f"WASP-{length}",
                    "units": "",
                    "type": "wasp",
                },
                "time_res": "monthly",
                "time_scale": length,
                "seas_len": None,
                "seas_daily": None,
                "calibration_period": [
                    arguments["start_year"],
                    arguments["end_year"],
                ],
                "minimum_reference_years": (
                    arguments["minimum_years"]
                ),
                "month_convention": (
                    "accumulation_ending_month"
                ),
                "normalization": (
                    "pooled_reference_window_stdev"
                ),
                "standard_deviation_ddof": 0,
                "geom": geometry,
            },
        },
    }

