
import numpy as np
import pandas as pd
import xarray as xr

from app.scripts._global import GLOBAL_CONFIG

from app.dst_api.scripts.spei_functions import (
    SPEI_Wrapper_setup,
)

from app.dst_api.scripts.spei_spatial import (
    spei_compute_params,
    spei_aggregate_data,
)


def _integer(params, key, minimum, maximum):
    value = params[key]

    if isinstance(value, bool):
        raise ValueError(f"Invalid parameter: {key}")

    number = int(value)

    if float(value) != number or not minimum <= number <= maximum:
        raise ValueError(f"Invalid parameter: {key}")

    return number


def _arguments(params):
    resolution = params.get(
        "timeRes",
        params.get("temporalRes", "monthly"),
    )

    if resolution != "monthly":
        raise ValueError("WASP requires monthly rainfall.")

    dataset = params["dataset"]

    if dataset not in GLOBAL_CONFIG["datasets"]:
        raise ValueError("Unknown rainfall dataset.")

    length = _integer(params, "timeScale", 1, 12)
    start = _integer(params, "startYear", 1, 9998)
    end = _integer(params, "endYear", 1, 9998)
    minimum = _integer(params, "minYear", 2, 9998)

    if start > end:
        raise ValueError(
            "Calibration start year exceeds the end year."
        )

    if minimum > end - start + 1:
        raise ValueError(
            "Minimum valid years exceeds the calibration period."
        )

    return {
        "dataset": dataset,
        "tscale": length,
        "start_year": start,
        "end_year": end,
        "minimum_years": minimum,
        "time_res": "monthly",
    }


def _prepare_monthly_rainfall(data):

    if not isinstance(data, xr.DataArray):
        raise TypeError(
            "Expected rainfall as an Xarray DataArray."
        )

    if "time" not in data.dims or data.sizes["time"] == 0:
        raise ValueError("No rainfall dates are available.")

    index = data.indexes["time"]

    if not index.is_unique or not index.is_monotonic_increasing:
        raise ValueError(
            "Expected unique, increasing monthly rainfall dates."
        )

    labels = np.asarray(
        data.time.dt.strftime("%Y-%m-01").values,
        dtype="datetime64[ns]",
    )

    if np.unique(labels).size != labels.size:
        raise ValueError(
            "Expected one rainfall observation per month. "
            "Aggregate daily or dekadal rainfall first."
        )

    data = data.assign_coords(time=labels)

    full_time = pd.date_range(
        start=pd.Timestamp(labels[0]),
        end=pd.Timestamp(labels[-1]),
        freq="MS",
    )

    data = data.reindex(time=full_time)

    return data.where(
        np.isfinite(data) & (data >= 0)
    )


def WASP_Wrapper_setup(precip, params):
    arguments = _arguments(params)

    setup = SPEI_Wrapper_setup(
        precip,
        {
            **params,
            "timeScale": arguments["tscale"],
            "timeRes": "monthly",
            "distribution": "zscore",
        },
    )

    return {
        **arguments,
        "tscale": setup["tscale"],
        "time_res": setup["time_res"],
    }


def WASP_Aggregate_data(data, tscale=1):

    if not 1 <= tscale <= 12:
        raise ValueError(
            "WASP accumulation must be 1 to 12 months."
        )

    data = data.where(np.isfinite(data))

    accumulated = spei_aggregate_data(
        data,
        tscale=tscale,
    )

    accumulated = accumulated.reindex(time=data.time)

    valid_count = data.notnull().rolling(
        time=tscale,
        min_periods=tscale,
    ).sum()

    return accumulated.where(
        valid_count == tscale
    ).transpose(*data.dims)


def WASP_Weighted_anomalies(precip, monthly_parameters):

    month = precip.time.dt.month

    mean = monthly_parameters["mean"].sel(month=month)
    sd = monthly_parameters["sd"].sel(month=month)

    annual_mean = monthly_parameters["mean"].sum(
        "month",
        skipna=False,
    )

    standardized = (
        (precip - mean)
        / sd.where(sd > 0)
    )


    standardized = xr.where(
        (sd == 0) & (precip == mean),
        0.0,
        standardized,
    )

    weighted = (
        standardized
        * mean
        / annual_mean.where(annual_mean > 0)
    )

    weighted = weighted.where(np.isfinite(precip))

    if "month" in weighted.coords:
        weighted = weighted.drop_vars("month")

    return weighted


def WASP_Compute_params(
    reference,
    tscale=12,
    min_non_na=30,
    ddof=0,
):
    """
    Reuse SPI z-score parameters for monthly rainfall statistics
    """
    if ddof not in (0, 1):
        raise ValueError("ddof must be 0 or 1.")

    reference = _prepare_monthly_rainfall(reference)

    monthly = spei_compute_params(
        reference,
        tscale=1,
        frequency=12,
        distribution="zscore",
        time_res="monthly",
        min_non_na=min_non_na,
    )

    monthly = monthly[["mean", "sd"]].rename(
        {"season": "month"}
    )

    # The existing SPI helper uses sample standard deviation (ddof=1)
    if ddof == 0:
        count = reference.groupby("time.month").count("time")

        correction = np.sqrt(
            (count - 1) / count.where(count > 0)
        )

        monthly["sd"] = monthly["sd"] * correction

    weighted = WASP_Weighted_anomalies(
        reference,
        monthly,
    )

    accumulated = WASP_Aggregate_data(
        weighted,
        tscale,
    )

    count = accumulated.count("time")

    normalization = accumulated.std(
        "time",
        skipna=True,
        ddof=ddof,
    )

    normalization = normalization.where(
        (count >= 2)
        & (normalization > 0)
        & np.isfinite(normalization)
    )

    result = monthly.assign(
        normalization=normalization
    )

    result.attrs.update({
        "analysis": "wasp",
        "time_scale": int(tscale),
        "time_resolution": "monthly",
        "standard_deviation_ddof": int(ddof),
        "normalization_method": "pooled_reference_window_stdev",
        "minimum_reference_years": int(min_non_na),
        "reference_start": str(
            reference.time.dt.strftime("%Y-%m").values[0]
        ),
        "reference_end": str(
            reference.time.dt.strftime("%Y-%m").values[-1]
        ),
    })

    return result


def WASP_Computation_ts(
    precip,
    fitted,
    tscale=12,
):
    """
    Apply WASP parameters to a point, selected cells, or a grid, default is whole country, to be verified here in the render map
    """
    if tscale != int(fitted.attrs["time_scale"]):
        raise ValueError(
            "WASP parameters use a different accumulation length."
        )

    weighted = WASP_Weighted_anomalies(
        precip,
        fitted,
    )

    accumulated = WASP_Aggregate_data(
        weighted,
        tscale,
    )

    wasp = accumulated / fitted["normalization"]
    wasp = wasp.where(np.isfinite(wasp)).rename("wasp")

    wasp.attrs.update({
        "units": "",
        "long_name": (
            "Weighted Anomaly of Standardized Precipitation"
        ),
        "time_scale": int(tscale),
        "time_resolution": "monthly",
        "month_convention": "accumulation_ending_month",
        "reference_start": fitted.attrs["reference_start"],
        "reference_end": fitted.attrs["reference_end"],
        "standard_deviation_ddof": (
            fitted.attrs["standard_deviation_ddof"]
        ),
        "normalization_method": (
            fitted.attrs["normalization_method"]
        ),
    })

    return wasp


def WASP_computation_wrapper(
    precip,
    params,
    fitted=None,
):
    """
    Follow SPI setup
    """
    precip = _prepare_monthly_rainfall(precip)
    setup = WASP_Wrapper_setup(precip, params)

    if fitted is None:
        reference = precip.sel(
            time=slice(
                f"{setup['start_year']:04d}-01-01",
                f"{setup['end_year']:04d}-12-31",
            )
        )

        if reference.sizes["time"] == 0:
            raise ValueError(
                "No rainfall within the calibration period."
            )

        fitted = WASP_Compute_params(
            reference,
            tscale=setup["tscale"],
            min_non_na=setup["minimum_years"],
            ddof=0,
        )

    return WASP_Computation_ts(
        precip,
        fitted,
        tscale=setup["tscale"],
    )

