#!/usr/bin/env python
# coding: utf-8


import csv

import pandas as pd


def mkdir(path):

    import os

    path = path.strip()
    path = path.rstrip("\\")
    is_exists = os.path.exists(path)
    if not is_exists:
        os.makedirs(path)
        return True
    else:
        return False


def get_zone():
    wind_west = ["UTC"]
    wind_east = ["UTC"]
    wind_texas = ["UTC"]
    solar_west = ["UTC"]
    solar_east = ["UTC"]
    solar_texas = ["UTC"]
    hydro_west = ["UTC"]
    hydro_east = ["UTC"]
    hydro_texas = ["UTC"]
    with open("HIFLD_Case_for_Profile_Input/plant.csv", "r") as f:
        reader = csv.reader(f)
        result = list(reader)
        for line in result:
            if line[26] == "hydro":
                if line[27] == "Eastern":
                    hydro_east.append(str(line[0]))
                elif line[27] == "Western":
                    hydro_west.append(str(line[0]))
                elif line[27] == "Texas":
                    hydro_texas.append(str(line[0]))
            elif line[26] == "solar":
                if line[27] == "Eastern":
                    solar_east.append(str(line[0]))
                elif line[27] == "Western":
                    solar_west.append(str(line[0]))
                elif line[27] == "Texas":
                    solar_texas.append(str(line[0]))
            elif line[26] == "wind" or line[26] == "wind_offshore":
                if line[27] == "Eastern":
                    wind_east.append(str(line[0]))
                elif line[27] == "Western":
                    wind_west.append(str(line[0]))
                elif line[27] == "Texas":
                    wind_texas.append(str(line[0]))

    return (
        wind_west,
        wind_east,
        wind_texas,
        solar_west,
        solar_east,
        solar_texas,
        hydro_west,
        hydro_east,
        hydro_texas,
    )


def devide_wind(wind_west, wind_east, wind_texas, east=False, west=False, texas=False):
    demand = pd.read_csv("output/HIFLD_Profiles_Final/wind.csv")
    if east:
        df = demand[wind_east]
        df.to_csv("output/HIFLD_Profiles_Final/eastern/wind.csv", index=False)
    if west:
        df = demand[wind_west]
        df.to_csv("output/HIFLD_Profiles_Final/western/wind.csv", index=False)
    if west:
        df = demand[wind_texas]
        df.to_csv("output/HIFLD_Profiles_Final/texas/wind.csv", index=False)


def devide_solar(
    solar_west, solar_east, solar_texas, east=False, west=False, texas=False
):
    demand = pd.read_csv("output/HIFLD_Profiles_Final/solar.csv")
    if east:
        df = demand[solar_east]
        df.to_csv("output/HIFLD_Profiles_Final/eastern/solar.csv", index=False)
    if west:
        df = demand[solar_west]
        df.to_csv("output/HIFLD_Profiles_Final/western/solar.csv", index=False)
    if west:
        df = demand[solar_texas]
        df.to_csv("output/HIFLD_Profiles_Final/texas/solar.csv", index=False)


def devide_hydro(
    hydro_west, hydro_east, hydro_texas, east=False, west=False, texas=False
):
    demand = pd.read_csv("output/HIFLD_Profiles_Final/hydro.csv")
    if east:
        df = demand[hydro_east]
        df.to_csv("output/HIFLD_Profiles_Final/eastern/hydro.csv", index=False)
    if west:
        df = demand[hydro_west]
        df.to_csv("output/HIFLD_Profiles_Final/western/hydro.csv", index=False)
    if west:
        df = demand[hydro_texas]
        df.to_csv("output/HIFLD_Profiles_Final/texas/hydro.csv", index=False)


if __name__ == "__main__":
    mkpath = "output\\HIFLD_Profiles_Final\\western\\"

    mkdir(mkpath)
    mkpath = "output\\HIFLD_Profiles_Final\\eastern\\"

    mkdir(mkpath)
    mkpath = "output\\HIFLD_Profiles_Final\\texas\\"

    mkdir(mkpath)
    (
        wind_west,
        wind_east,
        wind_texas,
        solar_west,
        solar_east,
        solar_texas,
        hydro_west,
        hydro_east,
        hydro_texas,
    ) = get_zone()
    devide_wind(wind_west, wind_east, wind_texas, east=True, west=True, texas=True)
    # devide_Solar(solar_West, solar_East, solar_Texas, east = False, west = False, texas = False)
    devide_hydro(hydro_west, hydro_east, hydro_texas, east=True, west=True, texas=True)
