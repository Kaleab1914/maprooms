
import hashlib
import json

from threading import Lock

import numpy as np
import pandas as pd
import xarray as xr

from app.scripts._global import GLOBAL_CONFIG
from app.scripts._cache import cache

from app.dst_api.scripts.zarrdata import get_zarr_dataset
from app.dst_api.scripts.aggregate_dataarray import xr_aggregate_data

from .wasp import (
    _arguments,
    _prepare_monthly_rainfall,
    WASP_Compute_params,
)


CACHE_VERSION = "health-wasp-v3"
CALIBRATION_LOCK = Lock()


def get_wasp_xr_data(params):
    """
    Load rainfall using the existing SPI dataset-loading structure.
    """
    arguments = _arguments(params)

    config = GLOBAL_CONFIG["datasets"][arguments["dataset"]]
    variable = config["variables"]["rainfall"]
    specification = config["monthly"]["netcdf"][variable]

    source_resolution = (
        specification["input"]
        if specification["compute"]
        else "monthly"
    )

    source_info = config[source_resolution]["netcdf"][variable]

    dataset = get_zarr_dataset({
        "dataset": arguments["dataset"],
        "temporalRes": "monthly",
        "variable": variable,
    })

    precip = dataset[variable]
    precip = precip.sortby("lat").sortby("lon")

    if set(precip.dims) != {"time", "lat", "lon"}:
        raise ValueError(
            "Expected rainfall dimensions: time, lat, and lon."
        )

    if precip.sizes["time"] == 0:
        raise ValueError("The rainfall dataset is empty.")

    index = precip.indexes["time"]

    if not index.is_unique or not index.is_monotonic_increasing:
        raise ValueError(
            "Expected unique, increasing rainfall dates."
        )

    units = str(
        precip.attrs.get("units")
        or source_info.get("units", "")
    ).strip().lower()

    if units not in ("mm", "mm/month", "mm/months"):
        raise ValueError(
            "WASP requires rainfall amounts in mm. "
            f"The source units are {units!r}."
        )

    precip = precip.where(
        np.isfinite(precip) & (precip >= 0)
    )

    # Timestamp counts require no rainfall-value computation.
    observations = xr.DataArray(
        np.ones(precip.sizes["time"]),
        coords={"time": precip.time},
        dims="time",
    ).resample(time="MS").sum()

    if specification["compute"]:
        if specification["function"] != "sum":
            raise ValueError(
                "Monthly rainfall must use sum aggregation."
            )

        precip = xr_aggregate_data(
            precip,
            aggr_fun="sum",
            in_res=source_resolution,
            out_res="monthly",
            min_frac=1.0,
        )

    precip = _prepare_monthly_rainfall(precip)

    if source_resolution == "daily":
        expected = observations.time.dt.days_in_month
    elif source_resolution == "dekadal":
        expected = 3
    elif source_resolution == "monthly":
        expected = 1
    else:
        raise ValueError(
            "Unsupported rainfall source resolution."
        )

    complete = observations == expected
    positions = np.flatnonzero(complete.values)

    if positions.size == 0:
        raise ValueError(
            "No complete monthly rainfall is available."
        )

    first = observations.time.values[positions[0]]
    last = observations.time.values[positions[-1]]

    precip = precip.sel(time=slice(first, last))

    complete = complete.reindex(
        time=precip.time,
        fill_value=False,
    )

    return precip.where(complete).transpose(
        "time",
        "lat",
        "lon",
    )


def get_wasp_parameters(precip, params):
    """
    Cache calibration fields
    """
    arguments = _arguments(params)

    reference = precip.sel(
        time=slice(
            f"{arguments['start_year']:04d}-01-01",
            f"{arguments['end_year']:04d}-12-31",
        )
    )

    if reference.sizes["time"] == 0:
        raise ValueError(
            "No rainfall within the calibration period."
        )


    signature = {
        "version": CACHE_VERSION,
        "arguments": arguments,
        "source": GLOBAL_CONFIG["datasets"][
            arguments["dataset"]
        ],
        "reference_dates": [
            str(reference.time.values[0]),
            str(reference.time.values[-1]),
        ],
        "reference_count": reference.sizes["time"],
        "shape": [
            precip.sizes["lat"],
            precip.sizes["lon"],
        ],
        "coordinates": {
            "lon": [
                float(precip.lon.values[0]),
                float(precip.lon.values[-1]),
            ],
            "lat": [
                float(precip.lat.values[0]),
                float(precip.lat.values[-1]),
            ],
        },
    }

    digest = hashlib.sha256(
        json.dumps(
            signature,
            sort_keys=True,
            default=str,
        ).encode()
    ).hexdigest()

    key = f"{CACHE_VERSION}:parameters:{digest}"

    fitted = cache.get(key)

    if fitted is not None:
        return fitted

    with CALIBRATION_LOCK:
        fitted = cache.get(key)

        if fitted is not None:
            return fitted

        tiles = []
        tile_size = 50

        for row in range(0, reference.sizes["lat"], tile_size):
            for column in range(0, reference.sizes["lon"], tile_size):
                tile = reference.isel(
                    lat=slice(row, row + tile_size),
                    lon=slice(column, column + tile_size),
                ).compute(scheduler="single-threaded")

                tile_parameters = WASP_Compute_params(
                    tile,
                    tscale=arguments["tscale"],
                    min_non_na=arguments["minimum_years"],
                    ddof=0,
                )

                tiles.append(tile_parameters)

        fitted = xr.combine_by_coords(
            tiles,
            combine_attrs="override",
        )

        cache.set(key, fitted, timeout=0)

        return fitted


def health_wasp_coverage_data(params):
    arguments = _arguments(params)
    precip = get_wasp_xr_data(params)

    length = arguments["tscale"]

    if precip.sizes["time"] < length:
        raise ValueError(
            "Insufficient rainfall for this accumulation."
        )

    first = pd.Timestamp(
        precip.time.values[length - 1]
    )
    last = pd.Timestamp(
        precip.time.values[-1]
    )

    return {
        "status": 0,
        "data": {
            "start": first.strftime("%Y-%m-%d"),
            "end": (
                last + pd.offsets.MonthEnd(0)
            ).strftime("%Y-%m-%d"),

            "plot_start_year": int(first.year),
            "plot_end_year": int(last.year),

            "map_start": pd.Timestamp(
                precip.time.values[0]
            ).strftime("%Y-%m-%d"),

            "map_end": (
                pd.Timestamp(precip.time.values[-length])
                + pd.offsets.MonthEnd(0)
            ).strftime("%Y-%m-%d"),
        },
    }



