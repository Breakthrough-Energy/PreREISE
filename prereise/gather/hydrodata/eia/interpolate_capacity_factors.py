import datetime
import os

import numpy as np
import pandas as pd


def get_profile(
    plant, start=pd.Timestamp(2016, 1, 1), end=pd.Timestamp(2016, 12, 31, 23)
):
    """Creates hydro profile from monthly capacity factors reported by EIA
    `here <https://www.eia.gov/electricity/annual/html/epa_04_08_b.html>`_.

    :param pandas.DataFrame plant: data frame with *'Pmax'* as column and
        *'plant_id'* as indices.
    :param pandas.Timestamp/numpy.datetime64/datetime.datetime start: start date.
    :param pandas.Timestamp/numpy.datetime64/datetime.datetime end: end date.
    :return: (*pandas.DataFrame*) -- data frame with UTC timestamp as indices and plant
        id as column names. Values are the energy in MWh.
    :raises TypeError: if plant is not a data frame and/or dates are str.
    :raises ValueError: if dates are invalid and/or data frame does not have a *'Pmax'*
        column.
    """
    if not isinstance(plant, pd.DataFrame):
        raise TypeError("plant must be a pandas.DataFrame object")
    if "Pmax" not in plant.columns:
        raise ValueError("Pmax must be in the plant data frame")

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

    data = scaler.copy()
    for i in plant.index:
        data[i] = data.cf * plant.loc[i].Pmax

    data.drop("cf", inplace=True, axis=1)

    return data
