import numpy as np
import pandas as pd
from tqdm import tqdm

from helpers import get_power


def simple_imputation(data, wind_farm):
    """Impute missing data using a simple procedure. For each missing entry,
       the extrema of the U and V components of the wind speed of all non
       missing entries that have the same location, same month, same hour
       are first found for each missing entry. Then, a U and V value are
       randomly generated between the respective derived ranges.

       :param data: pandas DataFrame as returned by
       py:method:`rap.retrieve_data`.
       :param wind_farm: pandas DataFrame of wind farms
       :return: pandas DataFrame with missing entries imputed.
    """

    # Locate missing data
    to_impute = data[data.U.isna()].index.values

    # Timestamp of all entries in dataframe
    dates = pd.DatetimeIndex(data['ts'].values)

    n_target = len(wind_farm)
    for i, j in tqdm(enumerate(to_impute), total=len(to_impute)):
        if i % n_target == 0:
            year = dates[j].year
            month = dates[j].month
            day = dates[j].day
            hour = dates[j].hour
            select = data[(dates.month == month) &
                          (dates.hour == hour) &
                          (data.Pout != -99)]

        k = data.loc[j].plantID
        select_plant = select[select.plantID == k]

        minU, maxU = select_plant['U'].min(), select_plant['U'].max()
        minV, maxV = select_plant['V'].min(), select_plant['V'].max()
        data.at[j, 'U'] = minU + (maxU - minU) * np.random.random()
        data.at[j, 'V'] = minV + (maxV - minV) * np.random.random()
        wspd = np.sqrt(data.loc[j].U**2 + data.loc[j].V**2)
        capacity = wind_farm.loc[k].GenMWMax
        data.at[j, 'Pout'] = get_power(wspd, 'IEC class 2') * capacity

    # Write output in csv file
    name = "western_wind_output_2016_ts.csv"
    data.to_csv(name, header=None, index=False,
                columns=['tsID', 'plantID', 'Pout'])
