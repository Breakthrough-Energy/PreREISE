import numpy as np
import pandas as pd
from tqdm import tqdm

from prereise.gather.winddata.power_curves import (
    get_power,
    get_state_power_curves,
    get_turbine_power_curves,
)


def _check_curve(curve):
    allowed_curves = ["state", "IEC class 2"]
    if curve not in allowed_curves:
        err_msg = "curve not in allowed: " + ", ".join(allowed_curves)
        raise ValueError(err_msg)


def _find_to_impute(data):
    # Locate missing data
    to_impute = data[data.U.isna()].index
    if len(to_impute) == 0:
        print("No missing data")
        return
    else:
        return to_impute


def _select_similar(data, dates, j):
    year = dates[j].year
    month = dates[j].month
    hour = dates[j].hour
    select = data[
        (dates.year == year)
        & (dates.month == month)
        & (dates.hour == hour)
        & (pd.notna(data.Pout))
    ]
    return select


def simple(data, wind_farm, inplace=True, curve="state"):
    """Impute missing data using a simple procedure. For each missing entry,
    the extrema of the U and V components of the wind speed of all non missing
    entries that have the same location, same month, same hour are first found
    for each missing entry. Then, a U and V value are randomly generated
    between the respective derived ranges.

    :param pandas.DataFrame data: data frame as returned by
        :py:func:`prereise.gather.winddata.rap.rap.retrieve_data`.
    :param pandas.DataFrame wind_farm: data frame of wind farms.
    :param bool inplace: should the imputation be done in place.
    :param str curve: 'state' to use the state average, otherwise named curve.
    :return: (*pandas.DataFrame*) -- data frame with missing entries imputed.
    """

    _check_curve(curve)
    data_impute = data if inplace else data.copy()
    to_impute = _find_to_impute(data)
    if to_impute is None:
        return

    # Information on wind turbines & state average tubrine curves
    tpc = get_turbine_power_curves()
    spc = get_state_power_curves()

    # Timestamp of all entries in data frame
    dates = pd.DatetimeIndex(data.index.values)

    n_target = len(wind_farm)
    select = None
    for i, j in tqdm(enumerate(to_impute), total=len(to_impute)):
        if i % n_target == 0:
            select = _select_similar(data, dates, j)

        k = data.loc[j].plant_id
        select_plant = select[select.plant_id == k]

        min_u, max_u = select_plant["U"].min(), select_plant["U"].max()
        min_v, max_v = select_plant["V"].min(), select_plant["V"].max()
        data_impute.at[j, "U"] = min_u + (max_u - min_u) * np.random.random()
        data_impute.at[j, "V"] = min_v + (max_v - min_v) * np.random.random()
        wspd = np.sqrt(data.loc[j].U ** 2 + data.loc[j].V ** 2)
        normalized_power = get_power(tpc, spc, wspd, "IEC class 2")
        data_impute.at[j, "Pout"] = normalized_power

    if not inplace:
        return data_impute


def gaussian(data, wind_farm, inplace=True, curve="state"):
    """Impute missing data using gaussian distributions of U & V. For each
    missing entry, sample U & V based on mean and covariance of non-missing
    entries that have the same location, same month, and same hour.

    :param pandas.DataFrame data: data frame as returned by
        :py:func:`prereise.gather.winddata.rap.rap.retrieve_data`.
    :param pandas.DataFrame wind_farm: data frame of wind farms.
    :param bool inplace: should the imputation be done in place.
    :param str curve: 'state' to use the state average, otherwise named curve.
    :return: (*pandas.DataFrame*) -- data frame with missing entries imputed.
    """

    _check_curve(curve)
    data_impute = data if inplace else data.copy()
    to_impute = _find_to_impute(data)
    if to_impute is None:
        return

    # Information on wind turbines & state average tubrine curves
    tpc = get_turbine_power_curves()
    spc = get_state_power_curves()

    # Timestamp of all entries in data frame
    dates = pd.DatetimeIndex(data.index.values)

    n_target = len(wind_farm)
    select = None
    for i, hour in tqdm(enumerate(to_impute), total=len(to_impute)):
        # Only run the similar-selection function the first time
        if i % n_target == 0:
            select = _select_similar(data, dates, hour)

        plant_id = data.loc[hour].plant_id
        select_plant = select[select.plant_id == plant_id]

        uv_data = np.array([select_plant["U"].to_numpy(), select_plant["V"].to_numpy()])
        cov = np.cov(uv_data)
        mean = np.mean(uv_data, axis=1)
        sample = np.random.multivariate_normal(mean=mean, cov=cov, size=1)
        data_impute.at[hour, "U"] = sample[0][0]
        data_impute.at[hour, "V"] = sample[0][1]

        wspd = np.sqrt(data.loc[hour].U ** 2 + data.loc[hour].V ** 2)
        normalized_power = get_power(tpc, spc, wspd, "IEC class 2")
        data_impute.at[hour, "Pout"] = normalized_power

    if not inplace:
        return data_impute


def linear(data, inplace=True):
    """Given a 2D array, linearly interpolate any missing values column-wise.

    :param numpy.array/pandas.DataFrame data: data to interpolate.
    :param bool inplace: whether to modify the data inplace or return a modified copy.
    :return: (*None/pandas.DataFrame*) -- if ``inplace`` is False, data frame with
        missing entries imputed.
    """
    data_impute = data if inplace else data.copy()
    data_impute[:] = pd.DataFrame(data_impute).interpolate()
    if not inplace:
        return data_impute
