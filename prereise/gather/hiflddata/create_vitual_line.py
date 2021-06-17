import csv

import pandas as pd

coord_precision = ".9f"


def bus_branch_neigh(branches):
    """Generate a dictionary of neighbor buses for each bus.

    :param pandas.DataFrame branch: branch DataFrame from branch.csv
    :return: (*dict*) -- bus_nei, a dict of neighbor buses of each bus.
    """
    bus_nei = {}

    for br in branches.iloc:
        if br["from_bus_id"] in bus_nei:
            bus_nei[br["from_bus_id"]].append([br["to_bus_id"], br["rateA"], br["x"]])
        else:
            bus_nei[br["from_bus_id"]] = [[br["to_bus_id"], br["rateA"], br["x"]]]
        if br["to_bus_id"] in bus_nei:
            bus_nei[br["to_bus_id"]].append([br["from_bus_id"], br["rateA"], br["x"]])
        else:
            bus_nei[br["to_bus_id"]] = [[br["from_bus_id"], br["rateA"], br["x"]]]

    return bus_nei


def find_neigh(bus, depth, load, re):
    """Use BFS to find buses need to add branches.

    :param str bus: Id of the start bus.
    :param int depth: the depth of BFS search.
    :param float load: load of the start bus.
    :param str re: Interconnect of the start bus.
    """

    global new_branch_id
    global bus_line_total_capa
    if depth == 0:
        print(new_branch_id)
        return
    bus_capacity = bus_line_total_capa[bus]
    dup = int(1.5 * (load) / bus_capacity)
    for br in bus_nei[bus]:
        for i in range(dup):
            print(new_branch_id)
            add_branch[new_branch_id] = [bus, br[0], br[1], re, br[2]]
            new_branch_id = new_branch_id + 1
            bus_line_total_capa[bus] += br[1]
            bus_line_total_capa[br[0]] += br[1]
        find_neigh(br[0], depth - 1, load, re)


def new_branch(buses, bus_load, add_branch, new_branch_id, depth):
    """Calculate branches need to be added

    :param pandas.DataFrame buses: bus DataFrame from bus.csv.
    :param dict bus_load: a dict of loads assigned to each bus.
    :param int depth: the depth of BFS search.
    :return: (*dict*) -- add_branch: a dict of branches to be added.
    """
    global bus_line_total_capa
    for bu in buses.iloc:
        bus_capacity = bus_line_total_capa[bu["bus_id"]]
        re = bu["interconnect"]
        true_load = bus_load[bu["bus_id"]]
        if bus_capacity < 1.2 * (true_load):
            find_neigh(bu["bus_id"], depth, true_load, re)

    return add_branch


if __name__ == "__main__":
    branches = pd.read_csv("output/branch.csv")
    plants = pd.read_csv("output/plant.csv")

    buses = pd.read_csv("output/bus.csv")
    # subs = pd.read_csv('output/sub.csv')
    demands = pd.read_csv("data/demand.csv")
    demands = demands.drop("UTC Time", axis=1)

    bus_line_total_capa = {}
    # bus_load = buses.set_index('bus_id')['Pd'].to_dict()

    grouped = buses["Pd"].groupby(buses["zone_id"])
    sum_pd = grouped.sum().to_dict()

    max_demand = demands.max().to_dict()

    scaling_factor = {}
    for i in range(1, 53):
        scaling_factor[i] = max_demand[str(i)] / sum_pd[i]
    bus_nei = bus_branch_neigh(branches)
    # print(bus_nei)
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

    bus_pmax = plants["Pmax"].groupby(plants["bus_id"]).sum().to_dict()

    new_branch_id = 990001
    add_branch = {}

    add_branch = new_branch(buses, bus_load, add_branch, new_branch_id, 2)
    num = int(len(add_branch) / 100)

    loc = 0

    for br in add_branch:
        loc = loc + 1
        if (loc % num) == 0:
            print(loc / num, "%")
        # a = [[bu,1,0,0,0,0,zone_id,0,0,0,0,0,0,0,add_bus[bu][3],add_bus[bu][4]]]
        new = pd.DataFrame(
            {
                "branch_id": br,
                "from_bus_id": add_branch[br][0],
                "to_bus_id": add_branch[br][1],
                "r": 0,
                "x": add_branch[br][4],
                "b": 0,
                "rateA": add_branch[br][2],
                "rateB": 0,
                "rateC": 0,
                "ratio": 0,
                "angle": 0,
                "status": 0,
                "angmin": 0.0,
                "angmax": 0.0,
                "Pf": 0.0,
                "Qf": 0.0,
                "Qt": 0.0,
                "mu_Sf": 0.0,
                "mu_St": 0.0,
                "mu_angmin": 0.0,
                "mu_angmax": 0.0,
                "branch_device_type": "Line",
                "interconnect": add_branch[br][3],
            },
            index=[1],
        )
        branches = branches.append(new)
    branches.to_csv("output/branch.csv", index=False)
