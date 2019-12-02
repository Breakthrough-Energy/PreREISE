import math

import pandas as pd


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
