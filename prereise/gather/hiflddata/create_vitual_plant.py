"""
Read data 
        -- demand.csv  This file must be provided and the zones in this demand.csv must be consistent with the zone.csv
        --  bus.csv  sub.csv bus2sub.csv branch.csv plant.csv gencost.csv

Write data for grid simulation
        -- plant.csv, gencost.csv
Core Tasks
        -- ill plant: Pmax over 1500 or the assigned bus could not afford its Pmax
        -- 1 Calcualte load for each bus (CL4B)
        -- 2 Calcualte Pmax for each bus (CP4B), Pmax = \sum_{i \in Plants conneted with the Bus} Pmax_{i}
        -- 3 Divide ill plants into virtual plants (DP2vP) , default number = 5
Core Subtask        
        -- 1 CL4B
            -- 1.1 Calculate the total Pd in each zone
            -- 1.2 Calculate the max value for each zone in demand.csv
            -- 1.3 The load of a bus is pd * (max_demand / total Pd)
        -- 3 DP2vP
            -- 3.1 Calculate the total capacity for each bus
            -- 3.2 Calculate the avaiable extra load that each bus could afford
            -- 3.3 For ill plants, find 5 nearest buses that could afford its Pmax
            -- 3.4 Create 5 virtual smaller plants and assigned them to the 5 buses, delete the ill plant
"""

import pandas as pd

coord_precision = ".9f"


def avai_load(buses, bus_pmax, bus_line_total_capa):
    """Calculate the avaiable capacity for each bus

    :param pandas.DataFrame buses: branch DataFrame from bus.csv
    :param dict bus_pmax: a dict of buses' total load from linked plants.
    :param dict bus_line_total_capa: a dict of buses' total capacity of linked lines.
    :return: (*dict*) -- avaiable_load, a dict of the avaiable capacity for each bus.
    """
    avaiable_load = {}
    for bus in buses.iloc:
        bus_id = bus["bus_id"]
        bus_capacity = bus_line_total_capa[bus_id]
        # true_load = bus["true_load"]
        if bus_id in bus_pmax:
            pmax = bus_pmax[bus_id]
        else:
            pmax = 0.0
        # if(bus_capacity > 1.2*(pmax - true_load):
        # avaiable_load[bus_id] = bus_capacity - 1.2*(pmax)
        # avaiable_load[bus_id] = bus_capacity - 1.2*(pmax - true_load)
        if bus_capacity > 1.2 * (pmax):
            avaiable_load[bus_id] = bus_capacity - 1.2 * (pmax)
    return avaiable_load


def loc_of_sub(subs):
    """Get the latitude and longitude of substations, and the substations in the area of each zip code

    :param dict subs:  a dict of substations from sub.csv
    :return: (*dict*) -- LocOfsub_dict, dict mapping the geo coordinate (x,y) to substations.
    :return: (*dict*) -- ZipOfsub_dict, dict mapping the zip code to a group of substations.
    :return: (*dict*) -- ziplist, a list of dicts contain all zip codes in each interconnect.
    """
    loc_of_sub_dict = {}
    zip_of_sub_dict = {}
    zip_of_sub_dict["Eastern"] = {}
    zip_of_sub_dict["Western"] = {}
    zip_of_sub_dict["Texas"] = {}
    ziplist = {}
    ziplist["Eastern"] = []
    ziplist["Western"] = []
    ziplist["Texas"] = []

    for index, row in subs.iterrows():
        loc = (
            format(row["lat"], coord_precision),
            format(row["lon"], coord_precision),
        )

        sub = row["sub_id"]
        zi = row["zip"]
        re = row["interconnect"]

        if zi in zip_of_sub_dict[re]:
            list1 = zip_of_sub_dict[re][zi]
            list1.append(sub)
            zip_of_sub_dict[re][zi] = list1
        else:
            list1 = [sub]
            zip_of_sub_dict[re][zi] = list1

        if zi not in ziplist[re]:
            ziplist[re].append(zi)

        loc_of_sub_dict[sub] = loc

    ziplist["Eastern"] = sorted(ziplist["Eastern"])
    ziplist["Western"] = sorted(ziplist["Western"])
    ziplist["Texas"] = sorted(ziplist["Texas"])

    return loc_of_sub_dict, zip_of_sub_dict, ziplist


def new_plant(
    plants,
    pl_curve,
    bus_line_total_capa,
    bus_load,
    ziplist,
    zip_of_sub_dict,
    avaiable_load,
    add_plant,
    plant_remove,
    new_plant_id,
):
    """Calculate the plants to be created

    :param pandas.DataFrame plants:  plants from plant.csv.
    :param dict pl_curve:  a dict of consumption curve of plants.
    :param dict bus_line_total_capa: a dict of buses' total capacity of linked lines.
    :param dict bus_load: a dict of loads assigned to each bus.
    :param dict ziplist: a list of dicts contain all zip codes in each interconnect, returned by :func: `LocOfsub`.
    :param dict zip_of_sub_dict: dict mapping the zip code to a group of substations, returned by :func: `LocOfsub`.
    :param dict avaiable_load: a dict of the avaiable capacity for each bus, returned by :func: `avai_load`.

    :return: (*dict*) -- add_plant, a dict of plants need to be added.
    :return: (*dict*) -- plant_remove, a dict of plants need to be deleted.
    """
    for plant in plants.iloc:
        bus_capacity = bus_line_total_capa[plant["bus_id"]]
        true_load = bus_load[plant["bus_id"]]
        if (plant["Pmax"] > 1500) or bus_capacity < 1.2 * (plant["Pmax"] - true_load):
            print(plant["bus_id"])
            lat = plant["lat"]
            lon = plant["lat"]
            pmax = plant["Pmax"]
            pmin = plant["Pmin"]
            plant_type = plant["type"]
            re = plant["interconnect"]
            plant_zip = plant["zip"]
            plant_remove[plant["plant_id"]] = []
            nei_bus, avaiable_load = find_near_sub(
                lat, lon, pmax, re, plant_zip, ziplist, zip_of_sub_dict, avaiable_load
            )
            for bu in nei_bus:
                add_plant[new_plant_id] = [
                    pmax * 0.2,
                    pmin * 0.2,
                    bu,
                    re,
                    plant_type,
                    pl_curve[plant["plant_id"]][0],
                    pl_curve[plant["plant_id"]][1],
                    pl_curve[plant["plant_id"]][2],
                ]
                plant_remove[plant["plant_id"]].append(new_plant_id)
                new_plant_id = new_plant_id + 1
    return add_plant, plant_remove


def find_near_sub(
    lat, lon, pmax, re, plant_zip, ziplist, zip_of_sub_dict, avaiable_load
):
    """Find 5 nearest avaiable buses which can afford the load of plant

    :param float lat: the latitude of plant.
    :param float lon: the longitude of plant.
    :param float pmax: pmax of plant.
    :param str re: interconnect of plant.
    :param int plant_zip: zip code of plant.
    :param dict ziplist: a list of dicts contain all zip codes in each interconnect, returned by :func: `LocOfsub`.
    :param dict zip_of_sub_dict: dict mapping the zip code to a group of substations, returned by :func: `LocOfsub`.
    :param dict avaiable_load: a dict of the avaiable capacity for each bus, returned by :func: `avai_load`.

    :return: (*list*) -- nei_bus, a list of 5 nearest buses.
    :return: (*dict*) -- avaiable_load, a dict of the avaiable capacity for each bus.
    """
    standard = pmax
    nei_bus = []
    index = len(ziplist[re]) - 1
    shift = 0
    for i in range(len(ziplist[re])):
        if ziplist[re][i] >= plant_zip:
            index = i
            break
    while len(nei_bus) < 5:
        if index - shift < 0 and index + shift >= len(ziplist[re]):
            print("error plant")
            break
        if index - shift >= 0:
            zip_code = ziplist[re][index - shift]
            for sub in zip_of_sub_dict[re][zip_code]:
                if sub not in avaiable_load:
                    break
                if avaiable_load[sub] > standard:
                    nei_bus.append(sub)
                    avaiable_load[sub] = avaiable_load[sub] - standard
                    # print(sub)
                    if len(nei_bus) == 5:
                        break
        if shift == 0:
            shift = shift + 1
            continue
        if len(nei_bus) == 5:
            break
        if index + shift < len(ziplist[re]):
            zip_code = ziplist[re][index + shift]
            for sub in zip_of_sub_dict[re][zip_code]:
                if sub not in avaiable_load:
                    break
                if avaiable_load[sub] > standard:
                    nei_bus.append(sub)
                    avaiable_load[sub] = avaiable_load[sub] - standard
                    if len(nei_bus) == 5:
                        break
        shift = shift + 1
    return nei_bus, avaiable_load


def remove_plant(plants, plant_remove):
    """Update plant

    :param pandas.DataFrame plants:  plants from plant.csv.
    :param dict plant_remove, a dict of plants need to be deleted, returned by :func: `new_plant`.
    :return: (*pandas.DataFrame*) -- plants, updated plants.
    """
    plants = plants[-plants.plant_id.isin(plant_remove)]
    return plants


def remove_gen(gencosts, plant_remove):
    """Update gencosts

    :param pandas.DataFrame gencosts:  plants from gencost.csv.
    :param dict plant_remove, a dict of plants need to be deleted, returned by :func: `new_plant`.
    :return: (*pandas.DataFrame*) -- gencosts, updated plants.
    """
    gencosts = gencosts[-gencosts.plant_id.isin(plant_remove)]
    return gencosts


if __name__ == "__main__":
    branches = pd.read_csv("output/branch.csv")
    plants = pd.read_csv("output/plant.csv")
    bus2sub = pd.read_csv("output/bus2sub.csv")
    buses = pd.read_csv("output/bus.csv")
    subs = pd.read_csv("output/sub.csv")
    demands = pd.read_csv("data/demand.csv")

    demands = demands.drop("UTC Time", axis=1)

    gencosts = pd.read_csv("output/gencost.csv")
    bus_line_total_capa = {}
    # bus_load = buses.set_index('bus_id')['Pd'].to_dict()

    grouped = buses["Pd"].groupby(buses["zone_id"])
    sum_pd = grouped.sum().to_dict()

    max_demand = demands.max().to_dict()

    scaling_factor = {}
    for i in range(1, 53):
        scaling_factor[i] = max_demand[str(i)] / sum_pd[i]

    bus_load = {}

    buses["true_load"] = ""
    # buses['total_capacity'] = ''

    for index in range(len(buses)):
        buses["true_load"][index] = (
            buses["Pd"][index] * scaling_factor[buses["zone_id"][index]]
        )
        bus_load[buses["bus_id"][index]] = buses["true_load"][index]

    for br in branches.iloc:
        if br["from_bus_id"] not in bus_line_total_capa:
            bus_line_total_capa[br["from_bus_id"]] = br["rateA"]
        else:
            bus_line_total_capa[br["from_bus_id"]] = (
                bus_line_total_capa[br["from_bus_id"]] + br["rateA"]
            )
        if br["to_bus_id"] not in bus_line_total_capa:
            bus_line_total_capa[br["to_bus_id"]] = br["rateA"]
        else:
            bus_line_total_capa[br["to_bus_id"]] = (
                bus_line_total_capa[br["to_bus_id"]] + br["rateA"]
            )
    LocOfsub_dict, ZipOfsub_dict, ziplist = loc_of_sub(subs)
    bus_pmax = plants["Pmax"].groupby(plants["bus_id"]).sum().to_dict()
    pl_curve = {}
    for pl in gencosts.iloc:
        cur = [pl["c2"], pl["c1"], pl["c0"]]
        pl_curve[pl["plant_id"]] = cur

    avaiable_load = avai_load(buses, bus_pmax, bus_line_total_capa)

    new_plant_id = 990001

    add_plant = {}
    plant_remove = {}

    add_plant, plant_remove = new_plant(
        plants,
        pl_curve,
        bus_line_total_capa,
        bus_load,
        ziplist,
        ZipOfsub_dict,
        avaiable_load,
        add_plant,
        plant_remove,
        new_plant_id,
    )

    for pl in add_plant:
        new = pd.DataFrame(
            {
                "plant_id": pl,
                "bus_id": add_plant[pl][2],
                "Pg": add_plant[pl][1],
                "Qg": 0,
                "Qmax": 0.0,
                "Qmin": 0.0,
                "Vg": 0,
                "mBase": 0,
                "status": 1,
                "Pmax": add_plant[pl][0],
                "Pmin": add_plant[pl][1],
                "Pc1": 0.0,
                "Pc2": 0.0,
                "Qc1min": 0.0,
                "Qc1max": 0.0,
                "Qc2min": 0.0,
                "Qc2max": 0.0,
                "ramp_agc": 0.0,
                "ramp_10": 0.0,
                "ramp_30": add_plant[pl][1],
                "ramp_q": 0.0,
                "apf": 0.0,
                "mu_Pmax": 0.0,
                "mu_Pmin": 0.0,
                "mu_Qmax": 0.0,
                "mu_Qmin": 0.0,
                "type": add_plant[pl][4],
                "interconnect": add_plant[pl][3],
                "GenFuelCost": 0.0,
                "GenIOB": 0.0,
                "GenIOC": 0.0,
                "GenIOD": 0.0,
                "distance": 0.0,
            },
            index=[1],
        )
        plants = plants.append(new)

    plants = remove_plant(plants, plant_remove)

    for pl in add_plant:

        new = pd.DataFrame(
            {
                "plant_id": pl,
                "type": 2,
                "startup": 0.0,
                "shutdown": 0,
                "n": 3.0,
                "c2": add_plant[pl][5],
                "c1": add_plant[pl][6],
                "c0": add_plant[pl][7],
                "interconnect": add_plant[pl][3],
            },
            index=[1],
        )
        gencosts = gencosts.append(new)

    gencosts = remove_gen(gencosts, plant_remove)

    plants.to_csv("output/plant.csv", index=False)
    gencosts.to_csv("output/gencost.csv", index=False)
