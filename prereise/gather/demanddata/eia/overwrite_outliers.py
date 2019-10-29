import pickle

df = pickle.load(open('eastern_agg_demand.pkl', 'rb'))

import numpy as np
from prereise.gather.demanddata.eia.find_fix_outliers import slope_interpolate

print('ISNE')
df_ISNE = slope_interpolate(df.iloc[:,0:1]) 
print('NYIS')
df_NYIS = slope_interpolate(df.iloc[:,1:2]) 
print('PJM')
df_PJM = slope_interpolate(df.iloc[:,2:3]) 
print('AEC')
df_AEC = slope_interpolate(df.iloc[:,3:4]) 
print('SOCO')
df_SOCO = slope_interpolate(df.iloc[:,4:5]) 
print('TVA_LGEE')
df_TVA_LGEE = slope_interpolate(df.iloc[:,5:6]) 
print('Florida')
df_Florida = slope_interpolate(df.iloc[:,6:7]) 
print('MISO')
df_MISO = slope_interpolate(df.iloc[:,7:8]) 
print('SWPP')
df_SWPP = slope_interpolate(df.iloc[:,8:9]) 
print('Carolina')
df_Carolina = slope_interpolate(df.iloc[:,9:10])

#drop unnecessary columns
import pandas as pd

df_ISNE.drop(['delta','delta_zscore'], axis=1, inplace=True)
df_NYIS.drop(['delta','delta_zscore'], axis=1, inplace=True)
df_PJM.drop(['delta','delta_zscore'], axis=1, inplace=True)
df_AEC.drop(['delta','delta_zscore'], axis=1, inplace=True)
df_SOCO.drop(['delta','delta_zscore'], axis=1, inplace=True)
df_TVA_LGEE.drop(['delta','delta_zscore'], axis=1, inplace=True)
df_Florida.drop(['delta','delta_zscore'], axis=1, inplace=True)
df_MISO.drop(['delta','delta_zscore'], axis=1, inplace=True)
df_SWPP.drop(['delta','delta_zscore'], axis=1, inplace=True)
df_Carolina.drop(['delta','delta_zscore'], axis=1, inplace=True)

frames = [df_ISNE, df_NYIS,df_PJM, df_AEC , df_SOCO, df_TVA_LGEE, df_Florida, df_MISO, df_SWPP, df_Carolina]
demand_interpolated = pd.concat(frames, axis = 1)

with open('demand_interpolated.pkl', 'wb') as handle:
  pickle.dump(demand_interpolated, handle, protocol=pickle.HIGHEST_PROTOCOL)