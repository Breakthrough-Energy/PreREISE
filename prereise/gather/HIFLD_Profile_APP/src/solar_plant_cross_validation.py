#!/usr/bin/env python
# coding: utf-8




import pandas as pd
def solar_plant_cross_validation():
    plants = pd.read_csv("HIFLD_Case_for_Profile_Input/plant.csv")
    tamu_origin_solar = pd.read_csv('output/PreReise_HIFLD_Profiles_Raw/solar.csv')
    standard_value = tamu_origin_solar['7442']

    standard_pmax = 100.0
    solar_plants = ['UTC']
    for plant in plants.iloc:
        if plant['type'] == 'solar':
            solar_plants.append(str(plant['plant_id']))
    tamu_origin_zone = [column for column in tamu_origin_solar]
    zone_not_exist = [i for i in tamu_origin_zone if i not in solar_plants]
    tamu_origin_solar.drop(zone_not_exist,axis=1)
    for plant in plants.iloc:
        if plant['type'] == 'solar' and str(plant['plant_id']) not in tamu_origin_zone:
                tamu_origin_solar[str(plant['plant_id'])] = standard_value*(plant['Pmax']/standard_pmax)
    tamu_origin_solar.to_csv('output/HIFLD_Profiles_Final/solar.csv')





if __name__ == '__main__':
    solar_plant_cross_validation()





