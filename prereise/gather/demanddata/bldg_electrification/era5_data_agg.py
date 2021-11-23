# This script contains functions to download ERA5 data and manipulate it to
# produce hourly time series of (dry bulb) temperature, dew point temperature
# and surface pressure. It is designed for the specific use case. For more
# general information on accessing ERA5 data, see:
# https://confluence.ecmwf.int/display/CKB/How+to+download+ERA5

import os

import cdsapi
import numpy as np
import pandas as pd
import xarray as xr
from scipy.spatial import cKDTree

from prereise.gather.demanddata.bldg_electrification import const

variable_names = {
    "temp": {"era5": "2m_temperature", "nc": "t2m"},
    "dewpt": {"era5": "2m_dewpoint_temperature", "nc": "d2m"},
    "pres": {"era5": "surface_pressure", "nc": "sp"},
}


def era5_download(years, directory, variable="temp"):
    """Download ERA5 data

    :param iterable year: year(s) for which data to be downloaded given as single
        value or iterable list
    :param str directory: path to root directory for ERA5 downloads
    :param str: variable to be downloaded, chosen from:
        temp {Default} -- dry bulb temperataure, corresponds to ERA5 variable "2m_temperature"
        dewpt -- dew point temperature, corresponds to ERA5 variable "2m_dewpoint_temperature"
        pres -- surface pressure, corresponds to ERA5 variable "surface_pressure"
    :raises ValueError: if the ``variable`` name is invalid or if any values in
        ``years`` are outside of the valid range.
    :raises Exception: if the cdsapi package is not configured properly.
    """

    # Check variable input and get associated ERA5 variable name
    try:
        variable_era5 = variable_names[variable]["era5"]
    except KeyError:
        raise ValueError(f"Invalid variable name: {variable}")

    # Make single year input iterable
    if not hasattr(years, "__iter__"):
        years = [years]

    # Error if 'years' includes any years prior to 1950
    if min(years) < 1950:
        raise ValueError("Input years must be 1950 or later")

    # Note if prior to 1979, preliminary version of reanalysis back extension
    if min(years) < 1979:
        print(
            "Data for years 1950-1979 are a preliminary version of reanalysis back extension"
        )

    try:
        c = cdsapi.Client()
    except Exception:
        raise Exception(
            "cdsapi is not configured properly, see https://cds.climate.copernicus.eu/api-how-to"
        )

    # Create folder to store data for given variable if it doesn't yet exist
    os.makedirs(os.path.join(directory, variable), exist_ok=True)

    for year in years:

        if year < 1979:
            dataset = "reanalysis-era5-single-levels-preliminary-back-extension"
        else:
            dataset = "reanalysis-era5-single-levels"

        print(
            f"Retrieving ERA5 {variable_era5} ({variable} input variable) dataset for {year}"
        )
        c.retrieve(
            dataset,
            {
                "product_type": "reanalysis",
                "format": "netcdf",
                "variable": variable_era5,
                "year": "{:04d}".format(year),
                "month": ["{:02d}".format(x) for x in range(1, 13)],
                "day": ["{:02d}".format(x) for x in range(1, 32)],
                "time": ["{:02d}:00".format(x) for x in range(0, 24)],
                "area": [50, -128, 24, -62],
            },
            os.path.join(directory, variable, f"{variable}s_era5_{year}.nc"),
        )


def create_era5_pumas(
    years, tract_puma_mapping, tract_pop, tract_lat_lon, directory, variable="temp"
):
    """Create {variable}s_pumas_{state}_{year}.csv or dewpt_pumas_{state}_{year} for all
        CONUS states and input year(s)

    :param iterable year: year(s) for which data files to be produced
    :param pandas.Series tract_puma_mapping: tract to puma mapping.
    :param pandas.Series tract_pop: population, indexed by tract.
    :param pandas.DataFrame tract_lat_lon: data frame, indexed by tract, with columns
        'state', 'lat', and 'lon'.
    :param str directory: path to root directory for ERA5 downloads (not including variable name)
    :param str: variable to produce
        temp {Default} -- dry bulb temperataure, corresponds to ERA5 variable "2m_temperature"
        dewpt -- dew point temperature, corresponds to ERA5 variable "2m_dewpoint_temperature"
        pres -- surface pressure, corresponds to ERA5 variable "surface_pressure"
    :raises ValueError: if the ``variable`` name is invalid.
    :raises FileNotFoundError: if not all required files are present.
    """
    # Function to convert latitude and longitude to cartesian coordinates
    def lon_lat_to_cartesian(lon, lat):

        # WGS 84 reference coordinate system parameters
        a = 6378.137  # major axis [km]
        e2 = 6.69437999014e-3  # eccentricity squared

        lon_rad = np.radians(lon)
        lat_rad = np.radians(lat)
        # convert to cartesian coordinates
        r_n = a / (np.sqrt(1 - e2 * (np.sin(lat_rad) ** 2)))
        x = r_n * np.cos(lat_rad) * np.cos(lon_rad)
        y = r_n * np.cos(lat_rad) * np.sin(lon_rad)
        z = r_n * (1 - e2) * np.sin(lat_rad)
        return x, y, z

    # Check variable input and get associated ERA5 variable name
    try:
        variable_era5 = variable_names[variable]["era5"]
        variable_nc = variable_names[variable]["nc"]
    except KeyError:
        raise ValueError(f"Invalid variable name: {variable}")

    # Make single year input iterable
    if not hasattr(years, "__iter__"):
        years = [years]

    # Check if ERA5 files exist for all input years
    n_missing = 0
    for year in years:
        if not os.path.exists(
            os.path.join(directory, variable, f"{variable}s_era5_{year}.nc")
        ):
            print(f"Missing file {variable_era5}_{year}.nc")
            n_missing = n_missing + 1
    if n_missing > 0:
        raise FileNotFoundError
    else:
        print("Confirmed: All required ERA5 input files present")

    # Create folder to store data for given variable if it doesn't yet exist
    os.makedirs(os.path.join(directory, "pumas", f"{variable}s"), exist_ok=True)

    # Combine tract-level data into single data frame
    tract_data = tract_lat_lon.assign(pop_2010=tract_pop, puma=tract_puma_mapping)
    # Filter to census tracts with building area data in included states
    tract_data = tract_data[tract_data["state"].isin(const.state_list)]

    # Loop through input years
    for year in years:
        print(f"Processing puma-level {variable} time series for {year}")
        # Load ERA5 dataset
        ds_era5 = xr.open_dataset(
            os.path.join(directory, variable, f"{variable}s_era5_{year}.nc")
        )

        # Get latitude and longitude from ERA5 dataset and make 2D arrays
        lats_era5 = ds_era5.variables["latitude"][:]
        lons_era5 = ds_era5.variables["longitude"][:]
        lons_era5_2d, lats_era5_2d = np.meshgrid(lons_era5, lats_era5)

        x_era5, y_era5, z_era5 = lon_lat_to_cartesian(
            lons_era5_2d.flatten(), lats_era5_2d.flatten()
        )
        x_tracts, y_tracts, z_tracts = lon_lat_to_cartesian(
            tract_data["lon"], tract_data["lat"]
        )

        # Create KD-tree from ERA5 dataset coordinates
        tree_era5 = cKDTree(np.column_stack((x_era5, y_era5, z_era5)))

        # Create tracts values time series data frame with interpoltion using inverse distance-squared weighting for 4 nearest neighbors
        d, inds = tree_era5.query(np.column_stack((x_tracts, y_tracts, z_tracts)), k=4)
        w = 1.0 / d ** 2
        vals_tracts = pd.Series(range(0, 8760)).apply(
            lambda x: pd.Series(
                (w * ds_era5[variable_nc][x].values.flatten()[inds]).sum(axis=1)
                / w.sum(axis=1),
                index=tract_data.index,
            )
        )

        state_pumas = const.puma_data.groupby("state")

        weighted_values = tract_data.groupby("puma").apply(
            lambda x: (vals_tracts[x.index] * x["pop_2010"]).sum(axis=1)
            / x["pop_2010"].sum()
        )
        # Convert units if needed (Kelvin to Celsius)
        if variable in {"temp", "dewpt"}:
            weighted_values -= 273.15
        # Loop through states
        for state in const.state_list:
            state_values = weighted_values.loc[state_pumas.get_group(state).index]
            state_values.T.to_csv(
                os.path.join(
                    directory,
                    "pumas",
                    f"{variable}s",
                    f"{variable}s_pumas_{state}_{year}.csv",
                ),
                index=False,
            )
