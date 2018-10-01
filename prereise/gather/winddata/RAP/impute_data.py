import numpy as np
import pandas as pd
from tqdm import tqdm

"""
Impute missing data in the RAP dataset.

The RAP dataframe is read, missing data are located and a simle procedure
is used for imputation.
"""

# Read dataframe
data = pd.read_pickle('western_wind_output_2016_unfilled.pkl')

# Locate missing data
to_impute = data[data.Pout == -99].index

# Timestamp of all entries in dataframe
dates = pd.DatetimeIndex(data['ts'].values)

# Impute missing data
# For each missing entry, the mean of the U and V components of the wind speed of all
# entries sharing the same site, month, hour and, of course, are not missing are located.
# U and V components of the missing entry is drawn from a uniform distribution bounded by
# the maximum values of U and V, respectively.
import westernintnet
grid = westernintnet.WesternIntNet()

wind_farm = grid.genbus.groupby('type').get_group('wind')
n_target = len(wind_farm)

PowerCurves = pd.read_csv('../IECPowerCurves.csv')

for i, j in tqdm(enumerate(to_impute)):
    if i % n_target == 0:
        year, month, day, hour = dates[j].year, dates[j].month, dates[j].day, dates[j].hour
        select = data[(dates.month == month) & (dates.hour == hour) & (data.Pout != -99)]

    k = data.loc[j].plantID
    select_plant = select[select.plantID == k]

    minU, maxU = select_plant['U'].min(), select_plant['U'].max()
    minV, maxV = select_plant['V'].min(), select_plant['V'].max()
    data.at[j,'U'] = minU + (maxU - minU) * np.random.random()
    data.at[j,'V'] = minV + (maxV - minV) * np.random.random()
    data.at[j,'Pout'] = get_power(np.sqrt(data.loc[j].U**2 + data.loc[j].V**2), 'IEC class 2') * wind_farm.loc[k].GenMWMax


# Save dataframe
data.to_pickle('western_wind_output_2016.pkl')

# Write output in csv file
name = "western_wind_output_2016_ts.csv"
data.to_csv(name, header=None, index=False, columns=['tsID','plantID','Pout'])



#############
# Functions #
#############

def get_power(wspd, turbine):
    """Convert wind speed to power using NREL turbine power curves.

    Arguments:
        wspd: wind speed (in m/s).
        turbine: class of turbine.

    Returns:
        Normalized power.
    """
    match  = (PowerCurves['Speed bin (m/s)'] <= np.ceil(wspd)) & (PowerCurves['Speed bin (m/s)'] >= np.floor(wspd))
    if not match.any():
        return 0
    values = PowerCurves[turbine][match]
    return np.interp(wspd,PowerCurves[turbine][match].index.values,PowerCurves[turbine][match].values)
