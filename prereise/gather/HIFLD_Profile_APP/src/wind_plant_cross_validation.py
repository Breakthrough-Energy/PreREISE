#!/usr/bin/env python
# coding: utf-8


import pandas as pd
def wind_plant_cross_validation():
    plants = pd.read_csv("HIFLD_Case_for_Profile_Input/plant.csv")
    tamu_origin_wind = pd.read_csv('output/PreReise_HIFLD_Profiles_Raw/wind.csv')
    standard_value = tamu_origin_wind['4670']
    standard_pg = 14.1
    standard_pmax = 278.0
    wind_plants = ['UTC']
    for plant in plants.iloc:
        if plant['type'] == 'wind' or plant['type'] == 'wind_offshore':
            wind_plants.append(str(plant['plant_id']))
    tamu_origin_zone = [column for column in tamu_origin_wind]
    zone_not_exist = [i for i in tamu_origin_zone if i not in wind_plants]
    tamu_origin_wind.drop(zone_not_exist,axis=1)
    for plant in plants.iloc:
        if (plant['type'] == 'wind' or plant['type'] == 'wind_offshore') and str(plant['plant_id']) not in tamu_origin_zone:
            if plant['Pg'] is not 0 and type(plant['Pg']) is not str:
                tamu_origin_wind[str(plant['plant_id'])] = standard_value*(plant['Pg']/standard_pg)
            else:
                tamu_origin_wind[str(plant['plant_id'])] = standard_value*(plant['Pmax']/standard_pmax)
    tamu_origin_wind.to_csv('output/HIFLD_Profiles_Final/wind.csv')




if __name__ == '__main__':
    wind_plant_cross_validation()





