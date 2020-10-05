from datetime import timedelta

import numpy as np
import pandas as pd
import PySAM.Pvwattsv7 as PVWatts
import PySAM.PySSC as pssc
from powersimdata.network.usa_tamu.constants.zones import (
    abv2interconnect,
    id2abv,
    interconnect2abv,
)
from tqdm import tqdm

from prereise.gather.solardata.helpers import get_plant_info_unique_location
from prereise.gather.solardata.pv_tracking import (
    get_pv_tracking_data,
    get_pv_tracking_ratio_state,
)


def retrieve_data(solar_plant, email, api_key, year="2016"):
    """Retrieves irradiance data from NSRDB and calculate the power output using
    the System Adviser Model (SAM).

    :param pandas.DataFrame solar_plant: data frame with *'lat'*, *'lon'* and
        *'Pmax' as columns and *'plant_id'* as index.
    :param str email: email used for API key
        `sign up <https://developer.nrel.gov/signup/>`_.
    :param str api_key: API key.
    :param str year: year.
    :return: (*pandas.DataFrame*) -- data frame with *'Pout'*, *'plant_id'*,
        *'ts'* and *'ts_id'* as columns. The power output is in MWh.
    """

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
    coord = get_plant_info_unique_location(solar_plant)

    base_url = "https://developer.nrel.gov/api/solar/nsrdb_psm3_download.csv"
    payload = {
        "api_key": api_key,
        "names": year,
        "leap_day": "false",
        "interval": "60",
        "utc": "true",
        "email": email,
        "attributes": "dhi,dni,wind_speed,air_temperature",
    }
    qs = "&".join([f"{key}={value}" for key, value in payload.items()])
    url = f"{base_url}?{qs}"

    data = pd.DataFrame({"Pout": [], "plant_id": [], "ts": [], "ts_id": []})

    # PV tracking ratios
    # By state and by interconnect when EIA data do not have any solar PV in
    # the state
    pv_info = get_pv_tracking_data()
    zone_id = solar_plant.zone_id.unique()
    frac = {}
    for i in zone_id:
        state = id2abv[i]
        frac[i] = get_pv_tracking_ratio_state(pv_info, [state])
        if frac[i] is None:
            frac[i] = get_pv_tracking_ratio_state(
                pv_info, list(interconnect2abv[abv2interconnect[state]])
            )

    # Inverter Loading Ratio
    ilr = 1.25

    for key in tqdm(coord.keys(), total=len(coord)):
        query = "wkt=POINT({lon}%20{lat})".format(lon=key[0], lat=key[1])
        current_url = f"{url}&{query}"

        info = pd.read_csv(current_url, nrows=1)
        tz, elevation = info["Local Time Zone"], info["Elevation"]

        data_resource = pd.read_csv(current_url, dtype=float, skiprows=2)
        data_resource.set_index(
            dates + timedelta(hours=int(tz.values[0])), inplace=True
        )

        # SAM
        ssc = pssc.PySSC()

        solar_data = {
            "lat": float(key[1]),
            "lon": float(key[0]),
            "tz": float(tz),
            "elev": float(elevation),
            "year": data_resource.index.year.tolist(),
            "month": data_resource.index.month.tolist(),
            "day": data_resource.index.day.tolist(),
            "hour": data_resource.index.hour.tolist(),
            "minute": data_resource.index.minute.tolist(),
            "dn": data_resource["DNI"].tolist(),
            "df": data_resource["DHI"].tolist(),
            "wspd": data_resource["Wind Speed"].tolist(),
            "tdry": data_resource["Temperature"].tolist(),
        }
        for i in coord[key]:
            data_site = pd.DataFrame(
                {
                    "ts": pd.date_range(
                        start="%s-01-01-00" % year, end="%s-12-31-23" % year, freq="H"
                    )
                }
            )
            data_site["ts_id"] = range(1, len(data_site) + 1)
            data_site["plant_id"] = i[0]

            power = 0
            for j, axis in enumerate([0, 2, 4]):
                pv_dict = {
                    # capacity in KW (DC)
                    "system_capacity": i[1] * 1000.0 * ilr,
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

                ratio = frac[solar_plant.loc[i[0]].zone_id][j]
                power += ratio * np.array(pv.Outputs.gen) / 1000

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
