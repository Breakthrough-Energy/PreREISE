import numpy as np
import pandas as pd
import PySAM.Pvwattsv7 as PVWatts
import PySAM.PySSC as pssc  # noqa: N813
from powersimdata.network.model import ModelImmutables
from tqdm import tqdm

from prereise.gather.solardata.helpers import get_plant_id_unique_location
from prereise.gather.solardata.nsrdb.nrel_api import NrelApi
from prereise.gather.solardata.pv_tracking import (
    get_pv_tracking_data,
    get_pv_tracking_ratio_state,
)


def retrieve_data(
    email,
    api_key,
    grid=None,
    solar_plant=None,
    grid_model=None,
    year="2016",
    rate_limit=0.5,
):
    """Retrieves irradiance data from NSRDB and calculate the power output using
    the System Adviser Model (SAM). Either a Grid object needs to be passed to ``grid``,
    or (a data frame needs to be passed to ``solar_plant`` and a string needs to be
    passed to ``grid_model``.

    :param str email: email used to`sign up <https://developer.nrel.gov/signup/>`_.
    :param str api_key: API key.
    :param powersimdata.input.grid.Grid: grid instance.
    :param pandas.DataFrame solar_plant: plant data frame.
    :param str grid_model: string used to populate grid model lookup tables.
    :param str year: year.
    :param int/float rate_limit: minimum seconds to wait between requests to NREL
    :return: (*pandas.DataFrame*) -- data frame with *'Pout'*, *'plant_id'*,
        *'ts'* and *'ts_id'* as columns. Values are power output for a 1MW generator.
    """
    xor_err_msg = "Either grid xor (solar_plant and grid_model) must be defined"
    if grid is None:
        if solar_plant is None or grid_model is None:
            raise TypeError(xor_err_msg)
        mi = ModelImmutables(grid_model)
    else:
        if solar_plant is not None or grid_model is not None:
            raise TypeError(xor_err_msg)
        solar_plant = grid.plant.query("type == 'solar'").copy()
        mi = grid.model_immutables

    # SAM only takes 365 days.
    try:
        leap_day = (pd.Timestamp("%s-02-29-00" % year).dayofyear - 1) * 24
        is_leap_year = True
        dates = pd.date_range(start="%s-01-01-00" % 2015, freq="H", periods=365 * 24)
        dates = dates.map(lambda t: t.replace(year=int(year)))
    except ValueError:
        leap_day = None
        is_leap_year = False
        dates = pd.date_range(start="%s-01-01-00" % year, freq="H", periods=365 * 24)

    # Identify unique location
    coord = get_plant_id_unique_location(solar_plant)

    data = pd.DataFrame({"Pout": [], "plant_id": [], "ts": [], "ts_id": []})

    # PV tracking ratios
    # By state and by interconnect when EIA data do not have any solar PV in
    # the state
    pv_info = get_pv_tracking_data()
    zone_id = solar_plant.zone_id.unique()
    frac = {}
    for i in zone_id:
        state = mi.zones["id2abv"][i]
        frac[i] = get_pv_tracking_ratio_state(pv_info, [state])
        if frac[i] is None:
            frac[i] = get_pv_tracking_ratio_state(
                pv_info,
                list(mi.zones["interconnect2abv"][mi.zones["abv2interconnect"][state]]),
            )

    # Inverter Loading Ratio
    ilr = 1.25
    api = NrelApi(email, api_key, rate_limit)

    for key in tqdm(coord.keys(), total=len(coord)):
        lat, lon = key[1], key[0]
        solar_data = api.get_psm3_at(
            lat,
            lon,
            attributes="dhi,dni,wind_speed,air_temperature",
            year=year,
            leap_day=False,
            dates=dates,
        ).to_dict()

        for i in coord[key]:
            data_site = pd.DataFrame(
                {
                    "ts": pd.date_range(
                        start="%s-01-01-00" % year, end="%s-12-31-23" % year, freq="H"
                    )
                }
            )
            data_site["ts_id"] = range(1, len(data_site) + 1)
            data_site["plant_id"] = i

            power = 0
            for j, axis in enumerate([0, 2, 4]):
                pv_dict = {
                    "system_capacity": ilr,
                    "dc_ac_ratio": ilr,
                    "tilt": 30,
                    "azimuth": 180,
                    "inv_eff": 94,
                    "losses": 14,
                    "array_type": axis,
                    "gcr": 0.4,
                    "adjust:constant": 0,
                }

                pv_dat = pssc.dict_to_ssc_table(pv_dict, "pvwattsv7")
                pv = PVWatts.wrap(pv_dat)
                pv.SolarResource.assign({"solar_resource_data": solar_data})
                pv.execute()

                ratio = frac[solar_plant.loc[i].zone_id][j]
                power += ratio * np.array(pv.Outputs.gen)

            if is_leap_year is True:
                data_site["Pout"] = np.insert(
                    power, leap_day, power[leap_day - 24 : leap_day]
                )
            else:
                data_site["Pout"] = power

            data = data.append(data_site, ignore_index=True, sort=False)

    data["plant_id"] = data["plant_id"].astype(np.int32)
    data["ts_id"] = data["ts_id"].astype(np.int32)

    data.sort_values(by=["ts_id", "plant_id"], inplace=True)
    data.reset_index(inplace=True, drop=True)

    return data
