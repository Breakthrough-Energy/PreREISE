import numpy as np
import pandas as pd
from pyproj import Proj


def ll2ij(lon_origin, lat_origin, lon, lat):
    """Finds nearest x/y indices for a given lat/lon.

    :param float lat_origin: latitude of coordinate of origin.
    :param float lon_origin: longitude of coordinate of origin.
    :param float lat: latitude of coordinate of interest.
    :param float lon: longitude of coordinate of interest.
    :return: (*tuple*) -- coordinate of the closest pixel in the database.
    """

    proj_string = """+proj=lcc +lat_1=30 +lat_2=60
                    +lat_0=38.47240422490422 +lon_0=-96.0
                    +x_0=0 +y_0=0 +ellps=sphere
                    +units=m +no_defs"""

    proj2grid = Proj(proj_string)

    origin_xy = proj2grid(lon_origin, lat_origin)
    target_xy = proj2grid(lon, lat)

    delta = np.subtract(target_xy, origin_xy)

    # 2-km grid resolution
    ij = [int(round(x/2000)) for x in delta]

    return tuple(reversed(ij))


def to_reise(data):
    """Formats data for REISE.

    :param pandas.DataFrame data: data frame as returned by
        :func:`prereise.gather.solardata.ga_wind.ga_wind.retrieve_data`.
    :return: (*pandas.DataFrame*) data frame formatted for REISE.
    """
    ts = data['ts'].unique()
    plant_id = data[data.ts_id == 1].plant_id.values

    profile = None
    for i in range(1, max(data.ts_id) + 1):
        data_tmp = pd.DataFrame({'Pout': data[data.ts_id == i].Pout.values},
                                index=plant_id)
        if i == 1:
            profile = data_tmp.T
        else:
            profile = profile.append(data_tmp.T, sort=False, ignore_index=True)

    profile.set_index(ts, inplace=True)
    profile.index.name = 'UTC'

    return profile
