#!/usr/bin/env python
# coding: utf-8

import pandas as pd


def mkdir(path):

    import os

    path = path.strip()
    path = path.rstrip("\\")
    isExists = os.path.exists(path)
    if not isExists:
        os.makedirs(path)
        return True
    else:
        return False


def solar_plant_cross_validation():
    hifldplants = pd.read_csv("HIFLD_Case_for_Profile_Input/plant.csv")
    hifldplants = hifldplants[hifldplants["type"] == "solar"]
    id_map_pmax = {}

    raw_solar = pd.read_csv("output/PreReise_HIFLD_Profiles_Raw/solar.csv")
    raw_solar.fillna(0.0)

    for plant in raw_solar:
        if plant == "UTC":
            continue
        for num in raw_solar[plant]:
            if float(num) < 0 or float(num) > 1000:
                raw_solar.drop(plant, axis=1)
                break

    solar_plants = ["UTC"]
    for plant in hifldplants.iloc:
        solar_plants.append(str(plant["plant_id"]))

    raw_plantname = [column for column in raw_solar]
    plant_not_exist_in_hifld = [i for i in raw_plantname if i not in solar_plants]
    raw_solar.drop(plant_not_exist_in_hifld, axis=1, inplace=True)

    pmax_list = sorted(hifldplants["Pmax"].drop_duplicates().to_list())
    # print(hifldplants['Pmax'].drop_duplicates().to_list())
    for plant in hifldplants.iloc:
        if (plant["Pmax"] not in id_map_pmax) and (
            str(plant["plant_id"]) in raw_plantname
        ):
            id_map_pmax[plant["Pmax"]] = str(plant["plant_id"])

    for plant in hifldplants.iloc:
        if str(plant["plant_id"]) not in raw_plantname:
            simpmax = 0.0
            for i in range(len(pmax_list)):
                if pmax_list[i] > plant["Pmax"]:
                    simpmax = pmax_list[i]
                    break
            if simpmax == 0.0:
                simpmax = pmax_list[-1]
            pid = id_map_pmax[simpmax]

            raw_solar[plant["plant_id"]] = raw_solar[pid] * (plant["Pmax"] / simpmax)
    raw_solar.to_csv("output/HIFLD_Profiles_Final/solar.csv", index=False)


if __name__ == "__main__":
    mkpath = "output\\HIFLD_Profiles_Final"

    mkdir(mkpath)
    solar_plant_cross_validation()
