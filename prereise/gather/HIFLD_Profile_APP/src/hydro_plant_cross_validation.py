#!/usr/bin/env python
# coding: utf-8



import pandas as pd
def hydro_plant_cross_validation():
    plants = pd.read_csv("HIFLD_Case_for_Profile_Input/plant.csv")
    tamu_origin_hydro = pd.read_csv('output/PreReise_HIFLD_Profiles_Raw/hydro.csv')
    standard_value = tamu_origin_hydro['539']
    standard_pg = 1.0
    standard_pmax = 6.0
    hydro_plants = ['UTC']
    for plant in plants.iloc:
        if plant['type'] == 'hydro':
            hydro_plants.append(str(plant['plant_id']))
    tamu_origin_zone = [column for column in tamu_origin_hydro]
    zone_not_exist = [i for i in tamu_origin_zone if i not in hydro_plants]
    tamu_origin_hydro.drop(zone_not_exist,axis=1)
    for plant in plants.iloc:
        if plant['type'] == 'hydro' and str(plant['plant_id']) not in tamu_origin_zone:
            tamu_origin_hydro[str(plant['plant_id'])] = standard_value*(plant['Pmax']/standard_pmax)
    tamu_origin_hydro.to_csv('output/HIFLD_Profiles_Final/hydro.csv')

if __name__ == '__main__':
    hydro_plant_cross_validation()






