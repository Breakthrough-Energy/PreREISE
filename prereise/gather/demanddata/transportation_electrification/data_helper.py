import numpy as np
import pandas as pd
from scipy.io import loadmat

from prereise.gather.demanddata.transportation_electrification import const


def get_model_year_dti(model_year: int):
    """Creates a DatetimeIndex based on the input year of the model.

    :param int model_year: the input year of the model
    :return: (*pandas.DatetimeIndex model_year_dti*) -- a DatetimeIndex encompassing the model year.
    """
    return pd.date_range(
        start=f"{model_year}-01-01", end=f"{model_year}-12-31", freq="D"
    )


def get_input_day(model_year_dti: pd.DatetimeIndex):
    """Determine whether each day of the model year is a weekend (1) or weekday (2)

    :param pandas.DatetimeIndex model_year_dti: a DatetimeIndex encompassing the model year.
    :return: (*numpy.ndarray*) -- array of 1s and 2s indicating weekend/weekday designations for the model year.
    """
    return model_year_dti.dayofweek.isin(range(5)).astype(int) + 1


def get_data_day(data: pd.DataFrame):
    """Get weekday/weekend designation value from data.

    :param pandas.DataFrame data: the data to get day of week from.
    :return: (*numpy.array*) -- indicates weekend or weekday for every day.
    """
    return np.array(data["If Weekend"])


def load_data(census_region: int, filepath: str = "nhts_census_updated.mat"):
    """Load the data at nhts_census.mat.

    :param int census_region: the census region to load data from.
    :param str filepath: the path to the matfile.
    :raises ValueError: if the census division is not between 1 and 9, inclusive.
    :return: (*pandas.DataFrame*) -- the data loaded from nths_census.mat, with column
        names added.
    """
    if not (1 <= census_region <= 9):
        raise ValueError("census_region must be between 1 and 9 (inclusive).")

    nhts_census = loadmat(filepath)
    raw_data = nhts_census[f"census_{census_region}_updated"]
    return pd.DataFrame(raw_data, columns=const.nhts_census_column_names)


def remove_ldt(data: pd.DataFrame):
    """Remove light duty trucks (vehicle types 4-6) from data loaded from nths_census.mat.
    Keep light duty vehicles (vehicle types 1-3).

    :param pandas.DataFrame data: the data returned from :func:`load_data`.
    :return: (*pandas.DataFrame*) -- the data loaded from :func:`load_data` with all rows
        involving LDT removed.
    """
    return data.loc[data["Vehicle type"].isin(range(1, 4))].copy()


def remove_ldv(data: pd.DataFrame):
    """Remove light duty vehicles (vehicle types 1-3) from data loaded from nths_census.mat.
    Keep light duty trucks (vehicle types 4-6).

    :param pandas.DataFrame data: the data returned from :func:`load_data`.
    :return: (*pandas.DataFrame*) -- the data loaded from :func:`load_data` with all rows
        involving LDT removed.
    """
    return data.loc[data["Vehicle type"].isin(range(4, 7))].copy()


def update_if_weekend(data: pd.DataFrame):
    """Updates the "If Weekend" values depending on the "Day of Week" value.
    Fridays and Sundays overlap into the weekend or weekday due to the
    vehicle time window, 6AM - 5:59AM.

    :param pandas.DataFrame data: the data returned from :func:`remove_ldt` or :func:`remove_ldv`.
    :return: (*pandas.DataFrame*) -- the data loaded from :func:`remove_ldt` or :func:`remove_ldv`
        with updated "If Weekend" values.
    """
    # weekend in the case of 1 or 7
    data.loc[data["Day of Week"].isin({1, 7}), "If Weekend"] = 1

    # weekday in the case of 2-6 (inclusive)
    data.loc[data["Day of Week"].isin(range(2, 7)), "If Weekend"] = 2

    return data
