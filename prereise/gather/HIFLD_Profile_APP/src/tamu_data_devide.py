#!/usr/bin/env python
# coding: utf-8




import csv
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
    wind_West = ['UTC']
    wind_East = ['UTC']
    wind_Texas = ['UTC']
    solar_West = ['UTC']
    solar_East = ['UTC']
    solar_Texas = ['UTC']
    hydro_West = ['UTC']
    hydro_East = ['UTC']
    hydro_Texas = ['UTC']
    with open('HIFLD_Case_for_Profile_Input/plant.csv', 'r') as f:
        reader = csv.reader(f)
        result = list(reader)
        for line in result:
            if line[10] == 'hydro':
                if line[9] == 'Eastern':
                    hydro_East.append(str(line[0]))
                elif line[9] == 'Western':
                    hydro_West.append(str(line[0]))
                elif line[9] == 'Texas':
                    hydro_Texas.append(str(line[0]))
            elif line[10] == 'solar':
                if line[9] == 'Eastern':
                    solar_East.append(str(line[0]))
                elif line[9] == 'Western':
                    solar_West.append(str(line[0]))
                elif line[9] == 'Texas':
                    solar_Texas.append(str(line[0]))
            elif line[10] == 'wind' or line[10] == 'wind_offshore':
                if line[9] == 'Eastern':
                    wind_East.append(str(line[0]))
                elif line[9] == 'Western':
                    wind_West.append(str(line[0]))
                elif line[9] == 'Texas':
                    wind_Texas.append(str(line[0]))

    return wind_West ,wind_East,wind_Texas ,solar_West ,solar_East ,solar_Texas,hydro_West ,hydro_East ,hydro_Texas 





def devide_Wind(wind_West, wind_East, wind_Texas, east = False, west = False, texas = False):
    demand = pd.read_csv('output/HIFLD_Profiles_Final/wind.csv')
    if (east):
        df = demand[wind_East]
        df.to_csv("output/HIFLD_Profiles_Final/eastern/wind.csv",index=False)
    if (west):
        df = demand[wind_West]
        df.to_csv("output/HIFLD_Profiles_Final/western/wind.csv",index=False)
    if (west):
        df = demand[wind_Texas]
        df.to_csv("output/HIFLD_Profiles_Final/texas/wind.csv",index=False)




def devide_Solar(solar_West, solar_East, solar_Texas, east = False, west = False, texas = False):
    demand = pd.read_csv('output/HIFLD_Profiles_Final/solar.csv')
    if (east):
        df = demand[solar_East]
        df.to_csv("output/HIFLD_Profiles_Final/eastern/solar.csv",index=False)
    if (west):
        df = demand[solar_West]
        df.to_csv("output/HIFLD_Profiles_Final/western/solar.csv",index=False)
    if (west):
        df = demand[solar_Texas]
        df.to_csv("output/HIFLD_Profiles_Final/texas/solar.csv",index=False)





def devide_Hydro(hydro_West, hydro_East, hydro_Texas, east = False, west = False, texas = False):
    demand = pd.read_csv('output/HIFLD_Profiles_Final/hydro.csv')
    if (east):
        df = demand[hydro_East]
        df.to_csv("output/HIFLD_Profiles_Final/eastern/hydro.csv",index=False)
    if (west):
        df = demand[hydro_West]
        df.to_csv("output/HIFLD_Profiles_Final/western/hydro.csv",index=False)
    if (west):
        df = demand[hydro_Texas]
        df.to_csv("output/HIFLD_Profiles_Final/texas/hydro.csv",index=False)





if __name__ == '__main__':
    mkpath="output\\HIFLD_Profiles_Final\\western\\"

    mkdir(mkpath)
    mkpath="output\\HIFLD_Profiles_Final\\eastern\\"

    mkdir(mkpath)
    mkpath="output\\HIFLD_Profiles_Final\\texas\\"

    mkdir(mkpath)
    wind_West ,wind_East,wind_Texas ,solar_West ,solar_East ,solar_Texas,hydro_West ,hydro_East ,hydro_Texas = get_Zone()
    devide_Wind(wind_West, wind_East, wind_Texas, east = True, west = True, texas = True)
    devide_Solar(solar_West, solar_East, solar_Texas, east = True, west = True, texas = True)
    devide_Hydro(hydro_West, hydro_East, hydro_Texas, east = True, west = True, texas = True)






