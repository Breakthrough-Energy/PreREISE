import datetime
import os

import numpy as np
import pandas as pd


def get_profile(
    plant_id, start=pd.Timestamp(2016, 1, 1), end=pd.Timestamp(2016, 12, 31, 23)
):
    """Creates hydro profile from monthly capacity factors reported by EIA
    `here <https://www.eia.gov/electricity/annual/html/epa_04_08_b.html>`_.

    :param list plant_id: id of the hydro plants.
    :param pandas.Timestamp/numpy.datetime64/datetime.datetime start: start date.
    :param pandas.Timestamp/numpy.datetime64/datetime.datetime end: end date.
    :return: (*pandas.DataFrame*) -- data frame with UTC timestamp as indices and plant
        id as column names. Values are the capacity factor. Note that a unique capacity
        factor is given for each month and for the entire US. Therefore, each plant
        will have the same profile.
    :raises TypeError: if plant_id is not a list and/or dates are str.
    :raises ValueError: if dates are invalid.
    """
    if not isinstance(plant_id, list):
        raise TypeError("plant_id must be a list")

    for d in [start, end]:
        if not isinstance(d, (pd.Timestamp, np.datetime64, datetime.datetime)):
            raise TypeError(
                "dates must be a pandas.Timestamp, a numpy.datetime64 or "
                "a datetime.datetime object"
            )

    filedir = os.path.join(os.path.join(os.path.dirname(__file__), ".."), "data")
    scaler = pd.read_csv(
        filedir + "/usa_hydro_capacity_factors.csv",
        header=None,
        index_col=0,
        names=["timestamp", "cf"],
    )
    scaler.index = pd.to_datetime(scaler.index)
    scaler = scaler.reindex(
        pd.date_range(start=scaler.index[0], end=scaler.index[-1], freq="H")
    )

    if start not in scaler.index:
        raise ValueError("Start date must be within [2015-01-15, 2017-12-15]")

    if end not in scaler.index:
        raise ValueError("End date must be within [2015-01-15, 2017-12-15]")

    if start >= end:
        raise ValueError("Start date must be greater than end date")

    scaler.interpolate(method="time", inplace=True)
    scaler = scaler[start:end]

    return pd.DataFrame({i: scaler.cf for i in plant_id}, index=scaler.index)
