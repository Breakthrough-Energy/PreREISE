import math
from os import path

import numpy as np
import pandas as pd

filename = 'PowerCurves.csv'
filepath = path.abspath(path.join(path.dirname(__file__), '..', filename))
PowerCurves = pd.read_csv(filepath, index_col=0, header=None).T


def ll2uv(lon, lat):
    """Convert (longitude, latitude) to unit vector.

    :param float lon: longitude of the site (in deg.) measured eastward from
        Greenwich, UK.
    :param float lat: latitude of the site (in deg.). Equator is the zero point.
    :return: (*tuple*) -- 3-components (x,y,z) unit vector.
    """
    cos_lat = math.cos(math.radians(lat))
    sin_lat = math.sin(math.radians(lat))
    cos_lon = math.cos(math.radians(lon))
    sin_lon = math.sin(math.radians(lon))

    uv = [cos_lat * cos_lon, cos_lat * sin_lon, sin_lat]

    return uv


def angular_distance(uv1, uv2):
    """Calculate the angular distance between two vectors.

    :param tuple uv1: 3-components vector as returned by :func:`ll2uv`.
    :param tuple uv2: 3-components vector as returned by :func:`ll2uv`.
    :return: (*float*) -- angle (in degrees).
    """
    cos_angle = uv1[0]*uv2[0] + uv1[1]*uv2[1] + uv1[2]*uv2[2]
    if cos_angle >= 1:
        cos_angle = 1
    if cos_angle <= -1:
        cos_angle = -1
    angle = math.degrees(math.acos(cos_angle))

    return angle


def get_power(wspd, turbine):
    """Convert wind speed to power using NREL turbine power curves.

    :param float wspd: wind speed (in m/s).
    :param str turbine: class of turbine.
    :return: (*float*) -- normalized power.
    """
    # "* 2" gives us ceil and floor with steps of 0.5
    match = (PowerCurves['Speed bin (m/s)'] * 2 <= np.ceil(wspd * 2)) & \
            (PowerCurves['Speed bin (m/s)'] * 2 >= np.floor(wspd * 2))
    if not any(match):
        return 0
    return np.interp(wspd,
                     PowerCurves[turbine][match].index.values,
                     PowerCurves[turbine][match].values)


def to_reise(data):
    """Format data for REISE.

    :param pandas.DataFrame data: data frame as returned by
        :func:`prereise.gather.winddata.rap.rap.retrieve_data`.
    :return: (*pandas.DataFrame*) -- data frame formatted for REISE.
    """
    ts = data['ts'].unique()
    plant_id = data[data.ts_id == 1].plant_id.values

    profile = None
    for i in range(1, max(data.ts_id)+1):
        data_tmp = pd.DataFrame({'Pout': data[data.ts_id == i].Pout.values},
                                index=plant_id)
        if i == 1:
            profile = data_tmp.T
        else:
            profile = profile.append(data_tmp.T, sort=False, ignore_index=True)

    profile.set_index(ts, inplace=True)
    profile.index.name = 'UTC'

    return profile
