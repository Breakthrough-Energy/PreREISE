#!/usr/bin/env python
# coding: utf-8


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
    west = []
    east = []
    texas = []
    zone = pd.read_csv("demand_input/zone.csv")
    for i in range(len(zone)):
        if zone["interconnect"][i] == "Eastern":
            east.append(str(zone["zone_id"][i]))
        elif zone["interconnect"][i] == "Western":
            west.append(str(zone["zone_id"][i]))
        else:
            texas.append(str(zone["zone_id"][i]))
    return west, east, texas


def devide_demand(
    west_interconnect,
    east_interconnect,
    texas_interconnect,
    east=False,
    west=False,
    texas=False,
):
    demand = pd.read_csv("demand_output/demand.csv")
    if east:
        df = demand.drop(west_interconnect, axis=1)
        df = df.drop(texas_interconnect, axis=1)
        df.to_csv("demand_output/eastern/demand.csv", index=False)
    if west:
        df = demand.drop(east_interconnect, axis=1)
        df = df.drop(texas_interconnect, axis=1)
        df.to_csv("demand_output/western/demand.csv", index=False)
    if texas:
        df = demand.drop(west_interconnect, axis=1)
        df = df.drop(east_interconnect, axis=1)
        df.to_csv("demand_output/texas/demand.csv", index=False)


if __name__ == "__main__":
    mkpath = "demand_output\\western\\"

    mkdir(mkpath)
    mkpath = "demand_output\\eastern\\"

    mkdir(mkpath)
    mkpath = "demand_output\\texas\\"

    mkdir(mkpath)
    west_interconnect, east_interconnect, texas_interconnect = get_zone()
    devide_demand(
        west_interconnect,
        east_interconnect,
        texas_interconnect,
        east=True,
        west=True,
        texas=True,
    )
