import numpy as np
import pandas as pd
import pygrib
from powersimdata.utility.distance import ll2uv
from scipy.spatial import KDTree
from tqdm import tqdm

from prereise.gather.winddata.hrrr.helpers import formatted_filename
from prereise.gather.winddata.impute import linear
from prereise.gather.winddata.power_curves import (
    get_power,
    get_state_power_curves,
    get_turbine_power_curves,
)

U_COMPONENT_SELECTOR = "U component of wind"
V_COMPONENT_SELECTOR = "V component of wind"


def get_wind_data_lat_long(dt, directory):
    """Returns the latitude and longitudes of the various
    wind grid sectors. Function assumes that there's data
    for the dt provided and the data lives in the directory.

    :param datetime.datetime dt: date and time of the grib data
    :param str directory: directory where the data is located
    :return: (*tuple*) -- A tuple of 2 same lengthed numpy arrays, first one being
        latitude and second one being longitude.
    """
    gribs = pygrib.open(directory + formatted_filename(dt))
    grib = next(gribs)
    return grib.latlons()


def find_closest_wind_grids(wind_farms, wind_data_lat_long):
    """Uses provided wind farm data and wind grid data to calculate
    the closest wind grid to each wind farm.

    :param pandas.DataFrame wind_farms: plant data frame.
    :param tuple wind_data_lat_long: A tuple of 2 same lengthed numpy arrays, first one being
        latitude and second one being longitude.
    :return: (*numpy.array*) -- a numpy array that holds in each index i
        the index of the closest wind grid in wind_data_lat_long for wind_farms i
    """
    grid_lats, grid_lons = (
        wind_data_lat_long[0].flatten(),
        wind_data_lat_long[1].flatten(),
    )
    assert len(grid_lats) == len(grid_lons)
    grid_lat_lon_unit_vectors = [ll2uv(i, j) for i, j in zip(grid_lons, grid_lats)]

    tree = KDTree(grid_lat_lon_unit_vectors)

    wind_farm_lats = wind_farms.lat.values
    wind_farm_lons = wind_farms.lon.values

    wind_farm_unit_vectors = [
        ll2uv(i, j) for i, j in zip(wind_farm_lons, wind_farm_lats)
    ]
    _, indices = tree.query(wind_farm_unit_vectors)

    return indices


def extract_wind_speed(wind_farms, start_dt, end_dt, directory):
    """Read wind speed from previously-downloaded files, and interpolate any gaps.

    :param pandas.DataFrame wind_farms: plant data frame.
    :param str start_dt: start date.
    :param str end_dt: end date (inclusive).
    :param str directory: directory where hrrr data is contained.
    :return: (*pandas.Dataframe*) -- data frame containing wind speed per wind farm
        on a per hourly basis between start_dt and end_dt inclusive. Structure of
        dataframe is:
            wind_farm1  wind_farm2
        dt1   speed       speed
        dt2   speed       speed
    """
    wind_data_lat_long = get_wind_data_lat_long(start_dt, directory)
    wind_farm_to_closest_wind_grid_indices = find_closest_wind_grids(
        wind_farms, wind_data_lat_long
    )
    dts = pd.date_range(start=start_dt, end=end_dt, freq="H").to_pydatetime()
    # Fetch wind speed data for each wind farm (or store NaN as applicable)
    wind_speed_data = pd.DataFrame(index=dts, columns=wind_farms.index, dtype=float)
    for dt in tqdm(dts):
        gribs = pygrib.open(formatted_filename(dt))
        try:
            u_component = gribs.select(name=U_COMPONENT_SELECTOR)[0].values.flatten()
            v_component = gribs.select(name=V_COMPONENT_SELECTOR)[0].values.flatten()
            wind_farm_specific_u_component = u_component[
                wind_farm_to_closest_wind_grid_indices
            ]
            wind_farm_specific_v_component = v_component[
                wind_farm_to_closest_wind_grid_indices
            ]
            wind_speed_data.loc[dt] = np.sqrt(
                pow(wind_farm_specific_u_component, 2)
                + pow(wind_farm_specific_v_component, 2)
            )
        except ValueError:
            # If the GRIB file is empty, no wind speed values can be selected
            wind_speed_data.loc[dt] = np.nan

    # For each column, linearly interpolate any NaN values
    linear(wind_speed_data)

    return wind_speed_data


def calculate_pout(wind_farms, start_dt, end_dt, directory):
    """Calculate power output for wind farms based on hrrr data.
    Function assumes that user has already called
    :meth:`prereise.gather.winddata.hrrr.hrrr.retrieve_data` with the same
    start_dt, end_dt, and directory.

    :param pandas.DataFrame wind_farms: plant data frame, plus 'state_abv' column.
    :param str start_dt: start date.
    :param str end_dt: end date (inclusive).
    :param str directory: directory where hrrr data is contained.
    :return: (*pandas.Dataframe*) -- Pandas containing power out per wind farm
        on a per hourly basis between start_dt and end_dt inclusive. Structure of
        dataframe is:
            wind_farm1  wind_farm2
        dt1    POUT        POUT
        dt2    POUT        POUT
    :raises ValueError: if ``wind_farms`` is missing the 'state_abv' column.
    """

    if "state_abv" not in wind_farms.columns:
        raise ValueError("The wind_farms data frame must have a 'state_abv' column")
    turbine_types = wind_farms.apply(
        lambda x: "Offshore" if x["type"] == "wind_offshore" else x["state_abv"], axis=1
    )

    turbine_power_curves = get_turbine_power_curves()
    state_power_curves = get_state_power_curves()

    # Read wind speed from previously-downloaded files, and interpolate
    wind_speed_data = extract_wind_speed(wind_farms, start_dt, end_dt, directory)
    dts = wind_speed_data.index

    # Then calculate wind power based on wind speed
    wind_power_data = [
        [
            get_power(
                turbine_power_curves,
                state_power_curves,
                wind_speed_data.loc[dt, w],
                turbine_types.loc[w],
            )
            for w in wind_farms.index
        ]
        for dt in tqdm(dts)
    ]
    df = pd.DataFrame(data=wind_power_data, index=dts, columns=wind_farms.index)

    return df
