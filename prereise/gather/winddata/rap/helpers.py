import math
import os

import numpy as np
import pandas as pd

PowerCurves = pd.read_csv(os.path.dirname(__file__) +
                          '/../IECPowerCurves.csv')


def ll2uv(lon, lat):
    """Convert (longitude, latitude) to unit vector.

    :param float lon: longitude of the site (in deg.) measured eastward from \ 
        Greenwich, UK.
    :param float lat: latitude of the site (in deg.). Equator is the zero \ 
        point.
    :return: (*tuple*) -- 3-components (x,y,z) unit vector.
    """
    cos_lat = math.cos(math.radians(lat))
    sin_lat = math.sin(math.radians(lat))
    cos_lon = math.cos(math.radians(lon))
    sin_lon = math.sin(math.radians(lon))

    uv = []
    uv.append(cos_lat * cos_lon)
    uv.append(cos_lat * sin_lon)
    uv.append(sin_lat)

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
    match = (PowerCurves['Speed bin (m/s)'] <= np.ceil(wspd)) & \
            (PowerCurves['Speed bin (m/s)'] >= np.floor(wspd))
    if not match.any():
        return 0
    values = PowerCurves[turbine][match]
    return np.interp(wspd,
                     PowerCurves[turbine][match].index.values,
                     PowerCurves[turbine][match].values)


def to_reise(data):
    """Format data for REISE.

    :param pandas data: data frame as returned \ 
        by :func:`prereise.gather.winddata.rap.rap.retrieve_data`.
    :return: (*pandas*) -- data frame formated for REISE.
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
