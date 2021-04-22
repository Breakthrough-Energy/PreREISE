#!/usr/bin/env python
# coding: utf-8



import pandas as pd


def mkdir(path):

    import os
    path=path.strip()
    path=path.rstrip("\\")
    isExists=os.path.exists(path)
    if not isExists:
        os.makedirs(path) 
        return True
    else:
        return False
 



def get_Zone():
    West = []
    East = []
    Texas = []
    zone = pd.read_csv('demand_input/zone.csv')
    for i in range(len(zone)):
        if(zone['interconnect'][i] == 'Eastern'):
            East.append(str(zone['zone_id'][i]))
        elif(zone['interconnect'][i] == 'Western'):
            West.append(str(zone['zone_id'][i]))
        else:
            Texas.append(str(zone['zone_id'][i]))
    return West, East, Texas




def devide_Demand(West, East, Texas, east = False, west = False, texas = False):
    demand = pd.read_csv('demand_output/demand.csv')
    if (east):
        df = demand.drop(West,axis=1)
        df = df.drop(Texas,axis=1)
        df.to_csv("demand_output/eastern/demand.csv",index=False)
    if (west):
        df = demand.drop(East,axis=1)
        df = df.drop(Texas,axis=1)
        df.to_csv('demand_output/western/demand.csv',index=False)
    if (texas):
        df = demand.drop(West,axis=1)
        df = df.drop(East,axis=1)
        df.to_csv('demand_output/texas/demand.csv',index=False)





if __name__ == '__main__':
    mkpath="demand_output\\western\\"

    mkdir(mkpath)
    mkpath="demand_output\\eastern\\"

    mkdir(mkpath)
    mkpath="demand_output\\texas\\"

    mkdir(mkpath)
    West, East, Texas = get_Zone()
    devide_Demand(West, East, Texas, east = True, west = True, texas = True)






