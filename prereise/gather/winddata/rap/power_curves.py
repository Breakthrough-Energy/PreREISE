import os
import re
from os import path

import numpy as np
import pandas as pd
from scipy.stats import norm

data_dir = path.abspath(path.join(path.dirname(__file__), "..", "data"))


def _shift_turbine_curve(turbine_curve, hub_height, maxspd, new_curve_res):
    """Shift a turbine curve based on a given hub height.

    :param pandas.Series turbine_curve: power curve data, wind speed index.
    :param float hub_height: height to shift power curve to.
    :param float maxspd: Extent of new curve (m/s).
    :param float new_curve_res: Resolution of new curve (m/s).
    """
    wspd_height_base = 262.467  # 80m in feet
    wspd_exp = 0.15  # wspd(h) = wspd_0 * (h / h0)**wspd_exp
    curve_x = np.arange(0, maxspd + new_curve_res, new_curve_res)
    wspd_scale_factor = (wspd_height_base / hub_height) ** wspd_exp
    shifted_x = turbine_curve.index * wspd_scale_factor
    shifted_curve = np.interp(curve_x, shifted_x, turbine_curve, left=0, right=0)
    shifted_curve = pd.Series(data=shifted_curve, index=curve_x)
    shifted_curve.index.name = "Speed bin (m/s)"
    return shifted_curve


def build_state_curves(form_860, power_curves, maxspd=30, default="IEC class 2", rsd=0):
    """Parse Form 860 and turbine curves to obtain average state curves.

    :param pandas.DataFrame form_860: EIA Form 860 data.
    :param pandas.DataFrame power_curves: turbine power curves.
    :param float maxspd: maximum x value for state curves.
    :param str default: turbine curve name for turbines not in power_curves.
    :param float rsd: relative standard deviation for spatiotemporal smoothing.
    :return: (*pandas.DataFrame*) - DataFrame of state curves.
    """
    print("building state_power_curves")
    mfg_col = "Predominant Turbine Manufacturer"
    model_col = "Predominant Turbine Model Number"
    capacity_col = "Nameplate Capacity (MW)"
    hubheight_col = "Turbine Hub Height (Feet)"
    new_curve_res = 0.01  # resolution: m/s

    states = form_860["State"].unique()
    curve_x = np.arange(0, maxspd + new_curve_res, new_curve_res)
    state_curves = pd.DataFrame(curve_x, columns=["Speed bin (m/s)"])
    for s in states:
        cumulative_curve = np.zeros_like(curve_x)
        cumulative_capacity = 0
        state_wind_farms = form_860[form_860["State"] == s]
        for i, f in enumerate(state_wind_farms.index):
            # Look up attributes from Form 860
            farm_capacity = state_wind_farms[capacity_col].iloc[i]
            hub_height = state_wind_farms[hubheight_col].iloc[i]
            turbine_mfg = state_wind_farms[mfg_col].iloc[i]
            turbine_model = state_wind_farms[model_col].iloc[i]
            # Look up turbine-specific power curve (or default)
            turbine_name = " ".join([turbine_mfg, turbine_model])
            if turbine_name not in power_curves.columns:
                turbine_name = default
            turbine_curve = power_curves[turbine_name]
            # Shift based on farm-specific hub height
            shifted_curve = _shift_turbine_curve(
                turbine_curve, hub_height, maxspd, new_curve_res
            )
            # Add to cumulative totals
            cumulative_curve += shifted_curve.to_numpy() * farm_capacity
            cumulative_capacity += farm_capacity
        # Normalize based on cumulative capacity
        state_curves[s] = cumulative_curve / cumulative_capacity
    state_curves.set_index("Speed bin (m/s)", inplace=True)

    # Add an 'Offshore' state with a representative curve
    hub_height = 393.701  # 120 meters, in feet to match Form860 data
    turbine_curve = power_curves["Vestas V164-8.0"]
    shifted_curve = _shift_turbine_curve(
        turbine_curve, hub_height, maxspd, new_curve_res
    )
    state_curves["Offshore"] = shifted_curve.to_numpy()
    offshore_rsd = 0.25

    if rsd > 0:
        smoothed_state_curves = pd.DataFrame(
            index=state_curves.index, columns=state_curves.columns
        )
        for s in state_curves.columns:
            xs = state_curves.index
            ys = np.zeros_like(xs)
            for i, x in enumerate(xs):
                if x == 0:
                    continue
                if s == "Offshore":
                    sd = max(1.5, offshore_rsd * x)
                else:
                    sd = max(1.5, rsd * x)
                min_point = x - 3 * sd
                max_point = x + 3 * sd
                sample_points = np.logical_and(xs > min_point, xs < max_point)
                cdf_points = norm.cdf(xs[sample_points], loc=x, scale=sd)
                pdf_points = np.concatenate((np.zeros(1), np.diff(cdf_points)))
                ys[i] = np.dot(pdf_points, state_curves[s][sample_points])
            smoothed_state_curves[s] = ys
        state_curves = smoothed_state_curves

    return state_curves


def get_form_860(data_dir, year=2016):
    """Read data for EIA Form 860.

    :param str data_dir: data directory.
    :param int year: EIA data year to get.
    :return: (*pandas.DataFrame*) -- dataframe with Form 860 data.
    """
    if not isinstance(data_dir, str):
        raise TypeError("data_dir is not a str")
    if not path.isdir(data_dir):
        raise ValueError("data_dir is not a valid directory")
    if not isinstance(year, int):
        raise TypeError("year is not an int")
    regex_str = r"3_2_Wind_Y(\d{4}).csv"
    valid_years = [
        int(re.match(regex_str, f).group(1))
        for f in os.listdir(data_dir)
        if re.match(regex_str, f)
    ]
    if year not in valid_years:
        err_msg = "form data for year {year} not found. ".format(year=year)
        err_msg += "Years with data: " + ", ".join(str(valid_years))
        raise ValueError(err_msg)

    form_860_filename = "3_2_Wind_Y{year}.csv".format(year=year)
    form_860_path = path.join(data_dir, form_860_filename)
    form_860 = pd.read_csv(form_860_path, skiprows=1)
    return form_860


def get_power(power_curves, state_power_curves, wspd, turbine, default="IEC class 2"):
    """Convert wind speed to power using NREL turbine power curves.

    :param pandas.DataFrame power_curves: turbine power curves data.
    :param pandas.DataFrame state_power_curves: state average power curves data.
    :param float wspd: wind speed (in m/s).
    :param str turbine: turbine name, IEC class, or state code for average.
    :param str default: default turbine name.
    :return: (*float*) -- normalized power.
    """
    if turbine in state_power_curves.columns:
        curve = state_power_curves[turbine]
    else:
        try:
            curve = power_curves[turbine]
        except KeyError:
            print(turbine, "not found, defaulting to", default)
            curve = power_curves[default]
    return np.interp(wspd, curve.index.values, curve.values, left=0, right=0)


def get_turbine_power_curves(filename="PowerCurves.csv"):
    """Load turbine power curves from csv.

    :param str filename: filename (not path) of csv file to read from.
    :return: (*pandas.DataFrame*) -- normalized turbine power curves.
    """
    powercurves_path = path.join(data_dir, filename)
    power_curves = pd.read_csv(powercurves_path, index_col=0, header=None).T
    power_curves.set_index("Speed bin (m/s)", inplace=True)
    return power_curves


def get_state_power_curves(filename="StatePowerCurves.csv", rsd=0.4):
    """Load state power curves from csv, if the csv is present. Otherwise,
    construct them from EIA form 860 data and turbine curves.

    :param str filename: filename (not path) of csv file to read from.
    :param float rsd: relative standard deviation, for wind speed distribution.
    :return: (*pandas.DataFrame*) -- normalized state power curves.
    """
    power_curves = get_turbine_power_curves()
    form_860 = get_form_860(data_dir)
    statepowercurves_path = path.join(data_dir, filename)
    try:
        state_power_curves = pd.read_csv(statepowercurves_path, index_col=0)
    except FileNotFoundError:
        state_power_curves = build_state_curves(form_860, power_curves, rsd=rsd)
        state_power_curves.to_csv(statepowercurves_path)
    return state_power_curves
