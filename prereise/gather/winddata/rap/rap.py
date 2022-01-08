import datetime
from collections import OrderedDict

import numpy as np
import pandas as pd
from netCDF4 import Dataset
from powersimdata.network.usa_tamu.constants.zones import id2abv
from powersimdata.utility.distance import angular_distance, ll2uv
from tqdm import tqdm

from prereise.gather.winddata.power_curves import (
    get_power,
    get_state_power_curves,
    get_turbine_power_curves,
)
from prereise.gather.winddata.rap.noaa_api import NoaaApi


def retrieve_data(wind_farm, start_date="2016-01-01", end_date="2016-12-31"):
    """Retrieve wind speed data from NOAA's server.

    :param pandas.DataFrame wind_farm: plant data frame.
    :param str start_date: start date.
    :param str end_date: end date (inclusive).
    :return: (*tuple*) -- First element is a pandas data frame with
        *'plant_id'*, *'U'*, *'V'*, *'Pout'*, *'ts'* and *'ts_id'* as columns.
        The power output is given for a 1MW generator and the U and V component of
        the wind speed 80-m above ground level are in m/s. Second element is a list
        of missing files.
    """

    # Define query box boundaries using the most northern, southern, eastern
    # and western. Add 1deg in each direction
    north_box = wind_farm.lat.max() + 1
    south_box = wind_farm.lat.min() - 1
    west_box = wind_farm.lon.min() - 1
    east_box = wind_farm.lon.max() + 1

    # Information on wind turbines & state average tubrine curves
    tpc = get_turbine_power_curves()
    spc = get_state_power_curves()

    # Information on wind farms
    n_target = len(wind_farm)

    lon_target = wind_farm.lon.values
    lat_target = wind_farm.lat.values
    id_target = wind_farm.index.values
    state_target = [
        "Offshore"
        if wind_farm.loc[i].type == "wind_offshore"
        else id2abv[wind_farm.loc[i].zone_id]
        for i in id_target
    ]

    start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.datetime.strptime(end_date, "%Y-%m-%d")

    box = {"north": north_box, "south": south_box, "west": west_box, "east": east_box}
    noaa = NoaaApi(box)
    url_count = len(noaa.get_path_list(start, end))

    missing = []
    target2grid = OrderedDict()
    size = url_count * n_target
    data = pd.DataFrame(
        {
            "plant_id": [0] * size,
            "ts": [np.nan] * size,
            "ts_id": [0] * size,
            "U": [0] * size,
            "V": [0] * size,
            "Pout": [0] * size,
        }
    )

    dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    step = datetime.timedelta(hours=1)

    def calc_angular_dist(lon_grid, lat_grid):
        n_grid = len(lon_grid)
        for j in range(n_target):
            uv_target = ll2uv(lon_target[j], lat_target[j])
            angle = [
                angular_distance(uv_target, ll2uv(lon_grid[k], lat_grid[k]))
                for k in range(n_grid)
            ]
            target2grid[id_target[j]] = np.argmin(angle)

    def handle_missing(response, data_tmp):
        missing.append(response.url)

        # missing data are set to NaN.
        data_tmp["U"] = [np.nan] * n_target
        data_tmp["V"] = [np.nan] * n_target
        data_tmp["Pout"] = [np.nan] * n_target

    first = True
    request_iter = enumerate(noaa.get_hourly_data(start, end))
    for i, response in tqdm(request_iter, total=url_count):

        data_tmp = pd.DataFrame(
            {"plant_id": id_target, "ts": [dt] * n_target, "ts_id": [i + 1] * n_target}
        )

        if response.status_code == 200:
            try:
                # see demo notebook to understand file structure
                tmp = Dataset("tmp.nc", "r", memory=response.content)
                lon_grid = tmp.variables["lon"][:].flatten()
                lat_grid = tmp.variables["lat"][:].flatten()
                u_wsp = tmp.variables[NoaaApi.var_u][0, 1, :, :].flatten()
                v_wsp = tmp.variables[NoaaApi.var_v][0, 1, :, :].flatten()

                if first:
                    # The angular distance is calculated once. The target to grid
                    # correspondence is stored in a dictionary.
                    calc_angular_dist(lon_grid, lat_grid)
                    first = False

                data_tmp["U"] = [
                    u_wsp[target2grid[id_target[j]]] for j in range(n_target)
                ]
                data_tmp["V"] = [
                    v_wsp[target2grid[id_target[j]]] for j in range(n_target)
                ]
                wspd_target = np.sqrt(pow(data_tmp["U"], 2) + pow(data_tmp["V"], 2))
                power = [
                    get_power(tpc, spc, wspd_target[j], state_target[j])
                    for j in range(n_target)
                ]
                data_tmp["Pout"] = power
            except Exception:
                print(f"Failed to parse response from url={response.url}")
                handle_missing(response, data_tmp)
        else:
            handle_missing(response, data_tmp)

        data.iloc[i * n_target : (i + 1) * n_target, :] = data_tmp.values
        dt += step

    # Format data frame
    data["plant_id"] = data["plant_id"].astype(np.int32)
    data["ts_id"] = data["ts_id"].astype(np.int32)
    data["U"] = data["U"].astype(np.float32)
    data["V"] = data["V"].astype(np.float32)
    data["Pout"] = data["Pout"].astype(np.float32)

    data.sort_values(by=["ts_id", "plant_id"], inplace=True)
    data.reset_index(inplace=True, drop=True)
    return data, missing
