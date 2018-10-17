import numpy as np
import pandas as pd
from pyproj import Proj


def ll2ij(lon_origin, lat_origin, lon, lat):
    """Find nearest x/y indices for a given lat/lon.

    :param lat: Latitude of coordinate of interest.
    :param lon: Longitude of coordinate of interest.
    :return: coordinate of the closest pixel in the database.
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
    """Format data for REISE.

    :param data: pandas DataFrame as returned by \ 
        :py:func:`prereise.gather.solardata.ga_wind.ga_wind.retrieve_data`.
    :return: pandas DataFrame formated for REISE.
    """
    ts = data['ts'].unique()
    plantID = data[data.tsID == 1].plantID.values

    for i in range(1, max(data.tsID)+1):
        data_tmp = pd.DataFrame({'Pout': data[data.tsID == i].Pout.values},
                                index=plantID)
        if i == 1:
            dataT = data_tmp.T
        else:
            dataT = dataT.append(data_tmp.T, sort=False, ignore_index=True)

    dataT.set_index(ts, inplace=True)
    dataT.index.name = 'UTC'

    return dataT
