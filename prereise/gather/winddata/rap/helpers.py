import math
from os import path

import numpy as np
import pandas as pd


def build_state_power_curves(filepath):
    """Parse Form 860 and turbine curves to obtain average state curves.

    :param str filepath: path for output file.
    :return: (*None*).
    """
    print('building state_power_curves')
    mfg_col = 'Predominant Turbine Manufacturer'
    model_col = 'Predominant Turbine Model Number'
    hubheight_col = 'Turbine Hub Height (Feet)'
    wspd_height_base = 262.467       #80m in feet
    wspd_exp = 0.15
    form_860_path = path.abspath(
        path.join(path.dirname(__file__), '..', '3_2_Wind_Y2016.csv'))

    form_860 = pd.read_csv(form_860_path, skiprows=1)
    states = form_860['State'].unique()
    base_x = PowerCurves['Speed bin (m/s)'].to_numpy()
    curve_x = np.arange(base_x[0], base_x[-1], 0.01)
    state_curves = pd.DataFrame(curve_x, columns=['Speed bin (m/s)'])
    for s in states:
        cumulative_curve = np.zeros_like(curve_x)
        cumulative_capacity = 0
        state_wind_farms = form_860[form_860['State'] == s]
        for i, f in enumerate(state_wind_farms.index):
            farm_capacity = state_wind_farms['Nameplate Capacity (MW)'].iloc[i]
            hub_height = state_wind_farms[hubheight_col].iloc[i]
            wspd_scale_factor = (wspd_height_base / hub_height)**wspd_exp
            shifted_x = base_x * wspd_scale_factor
            turbine_mfg = state_wind_farms[mfg_col].iloc[i]
            turbine_model = state_wind_farms[model_col].iloc[i]
            turbine_name = ' '.join([turbine_mfg, turbine_model])
            if turbine_name in PowerCurves.columns:
                turbine_curve = PowerCurves[turbine_name]
            else:
                turbine_curve = PowerCurves['IEC class 2']
            shifted_curve = np.interp(
                curve_x, shifted_x, turbine_curve, left=0, right=0)
            cumulative_curve += shifted_curve * farm_capacity
            cumulative_capacity += farm_capacity
        average_curve = cumulative_curve / cumulative_capacity
        state_curves[s] = average_curve
    state_curves.set_index('Speed bin (m/s)', inplace=True)
    state_curves.to_csv(filepath)


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


def get_power(wspd, turbine, default='IEC class 2'):
    """Convert wind speed to power using NREL turbine power curves.

    :param float wspd: wind speed (in m/s).
    :param str default: default turbine name.
    :param str turbine: turbine name, IEC class, or state code for average.
    :return: (*float*) -- normalized power.
    """

    if turbine in StatePowerCurves.index:
        curve = StatePowerCurves[turbine]
    else:
        try:
            curve = PowerCurves[turbine]
        except KeyError:
            print(turbine, 'not found, defaulting to', default)
            curve = PowerCurves[default]
    return np.interp(wspd, curve.index.values, curve.values, left=0, right=0)

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


filename = 'PowerCurves.csv'
filepath = path.abspath(path.join(path.dirname(__file__), '..', filename))
PowerCurves = pd.read_csv(filepath, index_col=0, header=None).T

filename = 'StatePowerCurves.csv'
filepath = path.abspath(path.join(path.dirname(__file__), '..', filename))
if not path.isfile(filepath):
    build_state_power_curves(filepath)
StatePowerCurves = pd.read_csv(filepath)
