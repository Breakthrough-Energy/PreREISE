import math
from os import path

import numpy as np
import pandas as pd


def _shift_turbine_curve(turbine_curve, hub_height, maxspd, new_curve_res):
    """Shift a turbine curve based on a given hub height.

    :param pandas.Series turbine_curve: power curve data, wind speed index.
    :param float hub_height: height to shift power curve to.
    :param float maxspd: Extent of new curve (m/s).
    :param float new_curve_res: Resolution of new curve (m/s).
    """
    wspd_height_base = 262.467      # 80m in feet
    wspd_exp = 0.15                 # wspd(h) = wspd_0 * (h / h0)**wspd_exp
    curve_x = np.arange(0, maxspd + new_curve_res, new_curve_res)
    wspd_scale_factor = (wspd_height_base / hub_height)**wspd_exp
    shifted_x = turbine_curve.index * wspd_scale_factor
    shifted_curve = np.interp(
        curve_x, shifted_x, turbine_curve, left=0, right=0)
    return shifted_curve

def build_state_curves(Form860, PowerCurves, maxspd=30, default='IEC class 2'):
    """Parse Form 860 and turbine curves to obtain average state curves.

    :param pandas.DataFrame Form860: EIA Form 860 data.
    :param pandas.DataFrame PowerCurves: turbine power curves.
    :param float maxspd: maximum x value for state curves.
    :param str default: turbine curve name for turbines not in PowerCurves.
    :return: (*pandas.DataFrame*) - DataFrame of state curves.
    """
    print('building state_power_curves')
    mfg_col = 'Predominant Turbine Manufacturer'
    model_col = 'Predominant Turbine Model Number'
    hubheight_col = 'Turbine Hub Height (Feet)'
    new_curve_res = 0.01            # resolution: m/s

    states = Form860['State'].unique()
    base_x = PowerCurves.index.to_numpy()
    curve_x = np.arange(0, maxspd + new_curve_res, new_curve_res)
    state_curves = pd.DataFrame(curve_x, columns=['Speed bin (m/s)'])
    for s in states:
        cumulative_curve = np.zeros_like(curve_x)
        cumulative_capacity = 0
        state_wind_farms = Form860[Form860['State'] == s]
        for i, f in enumerate(state_wind_farms.index):
            # Look up attributes from Form 860
            farm_capacity = state_wind_farms['Nameplate Capacity (MW)'].iloc[i]
            hub_height = state_wind_farms[hubheight_col].iloc[i]
            turbine_mfg = state_wind_farms[mfg_col].iloc[i]
            turbine_model = state_wind_farms[model_col].iloc[i]
            # Look up turbine-specific power curve (or default)
            turbine_name = ' '.join([turbine_mfg, turbine_model])
            if turbine_name not in PowerCurves.columns:
                turbine_name = default
            turbine_curve = PowerCurves[turbine_name]
            # Shift based on farm-specific hub height
            shifted_curve = _shift_turbine_curve(
                turbine_curve, hub_height, maxspd, new_curve_res)
            # Add to cumulative totals
            cumulative_curve += shifted_curve * farm_capacity
            cumulative_capacity += farm_capacity
        # Normalize based on cumulative capacity
        state_curves[s] = cumulative_curve / cumulative_capacity
    state_curves.set_index('Speed bin (m/s)', inplace=True)
    return state_curves


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


def get_form_860(data_dir, year=2016):
    """Read data for EIA Form 860.

    :param str data_dir: data directory.
    :param int year: EIA data year to get.
    :return: (*pandas.DataFrame*) -- dataframe with Form 860 data.
    """
    if not isinstance(data_dir, str):
        raise TypeError('data_dir is not a str')
    if not path.isdir(data_dir):
        raise ValueError('data_dir is not a valid directory')
    if not isinstance(year, int):
        raise TypeError('year is not an int')

    form_860_filename = ''.join(['3_2_Wind_Y', str(year), '.csv'])
    form_860_path = path.join(data_dir, form_860_filename)
    try:
        form_860 = pd.read_csv(form_860_path, skiprows=1)
    except FileNotFoundError:
        err_msg = ' '.join(['form data for year', str(year), 'not found.'])
        raise ValueError(err_msg)
    return form_860


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

data_dir = path.abspath(path.join(path.dirname(__file__), '..', 'data'))
Form860 = get_form_860(data_dir)
powercurves_path = path.join(data_dir, 'PowerCurves.csv')
PowerCurves = pd.read_csv(powercurves_path, index_col=0, header=None).T
PowerCurves.set_index('Speed bin (m/s)', inplace=True)
statepowercurves_path = path.join(data_dir, 'StatePowerCurves.csv')
try:
    StatePowerCurves = pd.read_csv(statepowercurves_path)
except FileNotFoundError:
    StatePowerCurves = build_state_curves(Form860, PowerCurves)
    StatePowerCurves.to_csv(statepowercurves_path)
