import argparse
from pathlib import Path

import xarray as xr
import yaml
from dask.diagnostics import ProgressBar


def convert_cmip6_units(data, variable):
    attrs = dict(data.attrs)
    source_units = str(attrs.get("units", "")).strip()

    if variable in ("tasmax", "tasmin", "tas"):
        if source_units in ("K", "kelvin", "Kelvin"):
            converted = data - 273.15

        elif source_units in (
            "°C",
            "degC",
            "degree_Celsius",
            "degrees_Celsius",
        ):
            converted = data.copy(deep=False)

        else:
            raise ValueError(
                f"Unsupported temperature units: {source_units!r}"
            )

        target_units = "°C"

    elif variable == "pr":
        if source_units in (
            "kg m-2 s-1",
            "kg m^-2 s^-1",
            "kg m**-2 s**-1",
        ):
            converted = data * 86400.0

        elif source_units in (
            "mm/day",
            "mm day-1",
            "mm d-1",
        ):
            converted = data.copy(deep=False)

        else:
            raise ValueError(
                f"Unsupported precipitation units: {source_units!r}"
            )

        target_units = "mm/day"

    else:
        raise ValueError(
            f"Unsupported CMIP6 variable: {variable!r}"
        )

    for key in (
        "valid_min",
        "valid_max",
        "valid_range",
        "actual_range",
    ):
        attrs.pop(key, None)

    attrs["original_units"] = source_units
    attrs["units"] = target_units
    converted.attrs = attrs

    return converted


def rechunk_dataset(dataset, chunks):
    dataset = dataset.copy(deep=False)

    for name in dataset.variables:
        variable = dataset[name]
        data = variable.data

        if not hasattr(data, "rechunk"):
            continue

        target_chunks = tuple(
            min(chunks.get(dimension, size), size)
            for dimension, size in zip(
                variable.dims,
                variable.shape,
                strict=True,
            )
        )
        dataset[name].data = data.rechunk(target_chunks)

    return dataset


def convert_cmip6_to_zarr(
    config_file,
    period,
    model,
    scenario=None,
    variable_key="maximum_temperature",
    bbox=None,
):
    # bbox = {'minLon': 30.625, 'maxLon': 50.375, 'minLat': 0.625, 'maxLat': 17.375}

    with Path(config_file).open(encoding="utf-8") as stream:
        config = yaml.safe_load(stream)["climate_projection"]

    source_root = Path(config["netcdf_dir"])
    target_root = Path(config["zarr_dir"])

    variable = config["variables"][variable_key]
    variable_info = config["netcdf"][variable]
    period_info = config[period]

    if period == "projection":
        if scenario not in config["scenarios"]:
            raise ValueError(
                "Specify a scenario listed in "
                "climate_projection.scenarios."
            )

    elif scenario is not None:
        raise ValueError(
            "Historical data do not require a scenario."
        )

    pattern = period_info["file_pattern"].format(
        folder=variable_info["folder"],
        model=model,
        scenario=scenario,
        varid=variable_info["varid"],
    )

    files = sorted(source_root.glob(pattern))

    if len(files) != 1:
        raise ValueError(
            f"Expected one combined NetCDF file; found {len(files)} "
            f"for {source_root / pattern}"
        )

    target = (
        target_root
        / variable_info["folder"]
        / period_info["directory"]
        / model
    )

    if period == "projection":
        target = target / scenario

    target = target / f"{variable}.zarr"

    if target.exists():
        raise FileExistsError(
            f"Output already exists: {target}"
        )

    with xr.open_dataset(files[0], chunks={}) as source:
        varid = variable_info["varid"]

        if varid not in source:
            raise ValueError(
                f"Variable {varid!r} is missing."
            )

        dimensions = {
            variable_info["time"],
            variable_info["lat"],
            variable_info["lon"],
        }

        if set(source[varid].dims) != dimensions:
            raise ValueError(
                f"Unexpected dimensions: {source[varid].dims}"
            )

        time_name = variable_info["time"]
        time_index = source.indexes[time_name]

        if (
            not time_index.is_unique
            or not time_index.is_monotonic_increasing
        ):
            raise ValueError(
                "Time coordinates must be unique and increasing."
            )

        time_encoding = {
            key: source[time_name].encoding[key]
            for key in ("units", "calendar", "dtype")
            if key in source[time_name].encoding
        }

        dataset = source.drop_encoding()

        rename = {
            original: standard
            for original, standard in (
                (variable_info["time"], "time"),
                (variable_info["lat"], "lat"),
                (variable_info["lon"], "lon"),
            )
            if original != standard
        }

        if rename:
            dataset = dataset.rename(rename)

        # Convert values and their units metadata.
        dataset[varid] = convert_cmip6_units(
            dataset[varid],
            variable,
        )

        dataset["time"].encoding.update(time_encoding)
        dataset = rechunk_dataset(dataset, config["chunks"])

        if bbox is not None:
            dataset = dataset.where(
                (dataset.lon >= bbox["minLon"])
                & (dataset.lon <= bbox["maxLon"])
                & (dataset.lat >= bbox["minLat"])
                & (dataset.lat <= bbox["maxLat"]),
                drop=True,
            )
            dataset = dataset.compute()

        target.parent.mkdir(parents=True, exist_ok=True)

        print(f"Input:  {files[0]}")
        print(f"Output: {target}")
        print(f"Units:  {dataset[varid].attrs['units']}")

        with ProgressBar():
            dataset.to_zarr(
                str(target),
                mode="w-",
                consolidated=False,
                zarr_format=2,
            )

    print("Conversion completed.")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Convert combined daily CMIP6 NetCDF files to Zarr, "
            "using °C for temperature and mm/day for precipitation."
        )
    )

    parser.add_argument(
        "--config",
        default=str(
            Path(__file__).resolve().parent
            / "app/yaml/datasets-config.yaml"
        ),
    )

    parser.add_argument(
        "--period",
        choices=["historical", "projection", "both"],
        default="both",
    )

    parser.add_argument("--model")
    parser.add_argument("--scenario")

    parser.add_argument(
        "--variable",
        choices=[
            "all",
            "maximum_temperature",
            "minimum_temperature",
            "rainfall",
        ],
        default="all",
    )

    args = parser.parse_args()

    with Path(args.config).open(encoding="utf-8") as stream:
        config = yaml.safe_load(stream)["climate_projection"]

    if args.scenario and args.scenario not in config["scenarios"]:
        parser.error(
            "Scenario is not listed in the dataset configuration."
        )

    if args.period == "historical" and args.scenario:
        parser.error(
            "Historical data do not require a scenario."
        )

    source_root = Path(config["netcdf_dir"])

    if not source_root.is_dir():
        parser.error(
            f"Source directory does not exist: {source_root}"
        )

    variables = (
        list(config["variables"])
        if args.variable == "all"
        else [args.variable]
    )

    periods = (
        ["historical", "projection"]
        if args.period == "both"
        else [args.period]
    )

    converted_count = 0
    skipped_count = 0
    discovered_count = 0

    for variable_key in variables:
        variable = config["variables"][variable_key]
        info = config["netcdf"][variable]

        for period in periods:
            period_info = config[period]

            root = (
                source_root
                / info["folder"]
                / period_info["directory"]
            )

            if not root.is_dir():
                continue

            model_directories = sorted(
                directory
                for directory in root.iterdir()
                if (
                    directory.is_dir()
                    and (
                        args.model is None
                        or directory.name == args.model
                    )
                )
            )

            if period == "historical":
                scenarios = [None]
            else:
                scenarios = (
                    [args.scenario]
                    if args.scenario
                    else list(config["scenarios"])
                )

            for directory in model_directories:
                model = directory.name

                for scenario in scenarios:
                    pattern = period_info["file_pattern"].format(
                        folder=info["folder"],
                        model=model,
                        scenario=scenario,
                        varid=info["varid"],
                    )

                    if not any(source_root.glob(pattern)):
                        continue

                    discovered_count += 1

                    try:
                        convert_cmip6_to_zarr(
                            args.config,
                            period,
                            model,
                            scenario,
                            variable_key=variable_key,
                            bbox=config["bbox"]
                        )

                    except FileExistsError as exc:
                        skipped_count += 1
                        print(f"Skipped: {exc}")

                    else:
                        converted_count += 1

    print(
        f"Finished: {discovered_count} datasets found, "
        f"{converted_count} converted, "
        f"{skipped_count} existing outputs skipped."
    )


if __name__ == "__main__":
    main()
