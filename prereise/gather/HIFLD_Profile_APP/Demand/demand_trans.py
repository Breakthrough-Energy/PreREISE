#!/usr/bin/env python
# coding: utf-8



import pandas as pd
import numpy as np

def agg_dic():
    z = pd.read_csv('demand_input/zone.csv')
    z_d ={}
    z_d1 = {}
    z1 = pd.read_csv('demand_input/zone_mapping.csv')
    for i in range(len(z)):
        tu = (z["state"][i], z["interconnect"][i])
        z_d[tu] = z["zone_id"][i]
    for i in range(len(z1)):
        tu = (z1["state"][i], z1["interconnect"][i])
        if tu == ('New Mexico','Eastern'):
            tu = ('New Mexico','Western')
        z_d1[str(z1["zone_id"][i])] = z_d[tu]
    
    return z_d1


if __name__ == '__main__':
    z_d1 = agg_dic()
    df = pd.read_csv('demand_input/base_demand.csv')
    df1 = pd.DataFrame(df['UTC Time'])
    for i in range(1,53):
        df1[i] = np.zeros(8784,dtype=int)
    for index in df.columns:
        if(index == 'UTC Time'):
            continue
        else:
            key = z_d1[index]
            df1[key] = df1[key] + df[index]

    df1[40] = 0.15 * df1[41]
    df1[40] = 0.85 * df1[41]
    df1.to_csv('demand_output/demand.csv', index=False)







