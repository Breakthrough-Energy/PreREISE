import numpy as np
import pandas as pd
from tqdm import tqdm

from helpers import get_power


def simple(data, wind_farm, inplace=True):
    """Impute missing data using a simple procedure. For each missing entry, \
    the extrema of the U and V components of the wind speed of all non \
    missing entries that have the same location, same month, same hour are \
    first found for each missing entry. Then, a U and V value are randomly \
    generated between the respective derived ranges.

    :param data: pandas DataFrame as returned by :py:func:`rap.retrieve_data`.
    :param wind_farm: pandas DataFrame of wind farms.
    :param bool inplace: should the imputation be done in place
    :return: pandas DataFrame with missing entries imputed.
    """

    if inplace:
        data_impute = data
    else:
        data_impute = data.copy()

    # Locate missing data
    to_impute = data[data.U.isna()].index
    if len(to_impute) == 0:
        print("No missing data")
        return

    # Timestamp of all entries in dataframe
    dates = pd.DatetimeIndex(data.index.values)

    n_target = len(wind_farm)
    for i, j in tqdm(enumerate(to_impute), total=len(to_impute)):
        if i % n_target == 0:
            year = dates[j].year
            month = dates[j].month
            day = dates[j].day
            hour = dates[j].hour
            select = data[(dates.year == year) &
                          (dates.month == month) &
                          (dates.hour == hour) &
                          (data.Pout != -99)]

        k = data.loc[j].plantID
        select_plant = select[select.plantID == k]

        minU, maxU = select_plant['U'].min(), select_plant['U'].max()
        minV, maxV = select_plant['V'].min(), select_plant['V'].max()
        data_impute.at[j, 'U'] = minU + (maxU - minU) * np.random.random()
        data_impute.at[j, 'V'] = minV + (maxV - minV) * np.random.random()
        wspd = np.sqrt(data.loc[j].U**2 + data.loc[j].V**2)
        capacity = wind_farm.loc[k].GenMWMax
        data_impute.at[j, 'Pout'] = get_power(wspd, 'IEC class 2') * capacity

    if not inplace:
        return data_impute
