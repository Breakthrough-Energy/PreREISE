import numpy as np
import pandas as pd
import PySAM.Pvwattsv8 as PVWatts
import PySAM.PySSC as pssc  # noqa: N813
from tqdm import tqdm

from prereise.gather.solardata.helpers import get_plant_id_unique_location
from prereise.gather.solardata.nsrdb.nrel_api import NrelApi
from prereise.gather.solardata.pv_tracking import (
    get_pv_tracking_data,
    get_pv_tracking_ratio_state,
)

default_pv_parameters = {
    "adjust:constant": 0,
    "azimuth": 180,
    "gcr": 0.4,
    "inv_eff": 94,
    "losses": 14,
    "tilt": 30,
}


def generate_timestamps_without_leap_day(year):
    """For a given year, return timestamps for each non-leap-day hour, and the timestamp
    of the beginning of the leap day (if there is one).

    :param int/str year: year to generate timestamps for.
    :return: (*tuple*) --
        pandas.DatetimeIndex: for each non-leap-day-hour of the given year.
        pandas.Timestamp/None: timestamp for the first hour of the leap day (if any).
    """
    # SAM only takes 365 days, so for a leap year: leave out the leap day.
    try:
        leap_day = (pd.Timestamp(f"{year}-02-29-00").dayofyear - 1) * 24
        sam_dates = pd.date_range(start=f"{year}-01-01-00", freq="H", periods=365 * 24)
        sam_dates = sam_dates.map(lambda t: t.replace(year=int(year)))
    except ValueError:
        leap_day = None
        sam_dates = pd.date_range(start=f"{year}-01-01-00", freq="H", periods=365 * 24)
    return sam_dates, leap_day


def calculate_power(solar_data, pv_dict):
    """Use PVWatts to translate weather data into power.

    :param dict solar_data: weather data as returned by :meth:`Psm3Data.to_dict`.
    :param dict pv_dict: solar plant attributes.
    :return: (*numpy.array*) hourly power output.
    """
    pv_dat = pssc.dict_to_ssc_table(pv_dict, "pvwattsv8")
    pv = PVWatts.wrap(pv_dat)
    pv.SolarResource.assign({"solar_resource_data": solar_data})
    pv.execute()
    return np.array(pv.Outputs.gen)


def retrieve_data_blended(
    email,
    api_key,
    grid=None,
    solar_plant=None,
    interconnect_to_state_abvs=None,
    year="2016",
    rate_limit=0.5,
    cache_dir=None,
):
    """Retrieves irradiance data from NSRDB and calculate the power output using
    the System Adviser Model (SAM). Either a Grid object needs to be passed to ``grid``,
    or (a data frame needs to be passed to ``solar_plant`` and a dictionary needs to be
    passed to ``interconnect_to_state_abvs``).

    :param str email: email used to`sign up <https://developer.nrel.gov/signup/>`_.
    :param str api_key: API key.
    :param powersimdata.input.grid.Grid: grid instance.
    :param pandas.DataFrame solar_plant: plant data frame.
    :param dict/pandas.Series interconnect_to_state_abvs: mapping of interconnection
        name to state abbreviations, used to look up average parameters by interconnect
        when average parameters by state are not available.
    :param int/str year: year.
    :param int/float rate_limit: minimum seconds to wait between requests to NREL
    :param str cache_dir: directory to cache downloaded data. If None, don't cache.
    :return: (*pandas.DataFrame*) -- data frame with *'Pout'*, *'plant_id'*,
        *'ts'* and *'ts_id'* as columns. Values are power output for a 1MW generator.
    """
    xor_err_msg = (
        "Either grid xor (solar_plant and interconnect_to_state_abvs) must be defined"
    )
    if grid is None:
        if solar_plant is None or interconnect_to_state_abvs is None:
            raise TypeError(xor_err_msg)
        if not {"state_abv", "interconnect"} <= set(solar_plant.columns):
            raise ValueError("solar_plant needs 'state_abv' and 'interconnect' columns")
        # Create mappings from other inputs
        zone_id_to_state_abv = {
            i: group["state_abv"].unique()[0]
            for i, group in solar_plant.groupby("zone_id")
        }
        zone_id_to_interconnect = {
            i: group["interconnect"].unique()[0]
            for i, group in solar_plant.groupby("zone_id")
        }
    else:
        if solar_plant is not None or interconnect_to_state_abvs is not None:
            raise TypeError(xor_err_msg)
        solar_plant = grid.plant.query("type == 'solar'").copy()
        # Use existing mappings found in the Grid object
        interconnect_to_state_abvs = grid.model_immutables.zones["interconnect2abv"]
        zone_id_to_state_abv = grid.model_immutables.zones["id2abv"]
        zone_id_to_interconnect = {
            z: grid.model_immutables.zones["abv2interconnect"][zone_id_to_state_abv[z]]
            for z in solar_plant["zone_id"].unique()
        }

    real_dates = pd.date_range(
        start=f"{year}-01-01-00", end=f"{year}-12-31-23", freq="H"
    )
    sam_dates, leap_day = generate_timestamps_without_leap_day(year)

    # PV tracking ratios
    # By state and by interconnect when EIA data do not have any solar PV in the state
    pv_info = get_pv_tracking_data()
    zone_id = solar_plant.zone_id.unique()
    frac = {}
    for zone in zone_id:
        state = zone_id_to_state_abv[zone]
        frac[zone] = get_pv_tracking_ratio_state(pv_info, [state])
        if frac[zone] is None:
            interconnect = zone_id_to_interconnect[zone]
            states_in_interconnect = list(interconnect_to_state_abvs[interconnect])
            frac[zone] = get_pv_tracking_ratio_state(pv_info, states_in_interconnect)

    # Inverter Loading Ratio
    ilr = 1.25
    api = NrelApi(email, api_key, rate_limit)

    # Identify unique location
    coord = get_plant_id_unique_location(solar_plant)

    data = {}
    for key, plants in tqdm(coord.items(), total=len(coord)):
        lat, lon = key[1], key[0]
        solar_data = api.get_psm3_at(
            lat,
            lon,
            attributes="dhi,dni,wind_speed,air_temperature",
            year=year,
            leap_day=False,
            dates=sam_dates,
            cache_dir=cache_dir,
        ).to_dict()

        for i, plant_id in enumerate(plants):
            if i == 0:
                # Calculate power for the first plant at each location
                first_plant_id = plant_id
                tracking_ratios = frac[solar_plant.loc[plant_id].zone_id]
                power = 0
                for j, axis in enumerate([0, 2, 4]):
                    plant_pv_dict = {
                        "system_capacity": ilr,
                        "dc_ac_ratio": ilr,
                        "array_type": axis,
                    }
                    pv_dict = {**default_pv_parameters, **plant_pv_dict}
                    power += tracking_ratios[j] * calculate_power(solar_data, pv_dict)
                if leap_day is not None:
                    power = np.insert(power, leap_day, power[leap_day - 24 : leap_day])
            else:
                # For every other plant, look up power from first plant at the location
                power = data[first_plant_id]
            data[plant_id] = power

    return pd.DataFrame(data, index=real_dates).sort_index(axis="columns")


def retrieve_data_individual(
    email, api_key, solar_plant, year="2016", rate_limit=0.5, cache_dir=None
):
    """Retrieves irradiance data from NSRDB and calculate the power output using
    the System Adviser Model (SAM). Either a Grid object needs to be passed to ``grid``,
    or (a data frame needs to be passed to ``solar_plant`` and a string needs to be
    passed to ``grid_model``.

    :param str email: email used to`sign up <https://developer.nrel.gov/signup/>`_.
    :param str api_key: API key.
    :param pandas.DataFrame solar_plant: plant data frame, plus additional boolean
        columns 'Single-Axis Tracking?', 'Dual-Axis Tracking?', 'Fixed Tilt?', and float
        columns 'Tilt Angle', 'Nameplate Capacity (MW)', and 'DC Net Capacity (MW)'.
    :param int/str year: year.
    :param int/float rate_limit: minimum seconds to wait between requests to NREL
    :param str cache_dir: directory to cache downloaded data. If None, don't cache.
    :return: (*pandas.DataFrame*) -- data frame with *'Pout'*, *'plant_id'*,
        *'ts'* and *'ts_id'* as columns. Values are power output for a 1MW generator.
    """
    # Verify that each solar plant has exactly one tracking type equal to True
    array_type_mapping = {
        "Fixed Tilt?": 0,
        "Single-Axis Tracking?": 2,
        "Dual-Axis Tracking?": 4,
    }
    if not all(solar_plant[array_type_mapping.keys()].sum(axis=1) == 1):
        raise ValueError("Indeterminate tracking information for one or more plants")
    # Select the appropriate 'array type' to pass to SAM
    plant_array_types = (
        solar_plant[array_type_mapping.keys()]
        .astype(bool)
        .apply(lambda x: array_type_mapping[x.idxmax()], axis=1)
    )

    real_dates = pd.date_range(
        start=f"{year}-01-01-00", end=f"{year}-12-31-23", freq="H"
    )
    sam_dates, leap_day = generate_timestamps_without_leap_day(year)

    api = NrelApi(email, api_key, rate_limit)

    coord = get_plant_id_unique_location(solar_plant)

    data = {}
    for key, plants in tqdm(coord.items(), total=len(coord)):
        lat, lon = key[1], key[0]
        solar_data = api.get_psm3_at(
            lat,
            lon,
            attributes="dhi,dni,wind_speed,air_temperature",
            year=year,
            leap_day=False,
            dates=sam_dates,
            cache_dir=cache_dir,
        ).to_dict()

        for plant_id in plants:
            series = solar_plant.loc[plant_id]
            ilr = series["DC Net Capacity (MW)"] / series["Nameplate Capacity (MW)"]
            plant_pv_dict = {
                "system_capacity": ilr,
                "dc_ac_ratio": ilr,
                "array_type": plant_array_types.loc[plant_id],
            }
            if plant_pv_dict["array_type"] == 0:
                plant_pv_dict["tilt"] = series["Tilt Angle"]
            pv_dict = {**default_pv_parameters, **plant_pv_dict}
            power = calculate_power(solar_data, pv_dict)
            if leap_day is not None:
                power = np.insert(power, leap_day, power[leap_day - 24 : leap_day])

            data[plant_id] = power

    return pd.DataFrame(data, index=real_dates).sort_index(axis="columns")
