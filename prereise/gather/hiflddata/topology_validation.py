"""
Read data  (data populated by data_trans.py)
        -- bus.csv  sub.csv bus2sub.csv branch.csv  zone.csv

Write data for grid simulation
        -- bus.csv  sub.csv bus2sub.csv branch.csv
Core Task
        -- Revise the ill buses and tranmission lines
        -- ill bus: in the wrong U.S. interconnect region
        -- ill tranmission line: connected with two different U.S. interconnect region
Preproces
        -- Create Hashmaps
            -- Map Bus ID to U.S. interconnect region
            -- Map Bus ID to U.S. State
Core Subtask
        -- ill branch set UNION normal branch set = whole branch set
        -- normal bus set UNION unlable bus set = whole bus set

        -- identify all ill branch
            -- a branch is ill when its two ends are in two different U.S. interconnect region
        -- identify all normal bus
            -- For each line, if the line is normal line, then the two ends of this line are normal bus
            -- The lable for normal bus cannot be changed once it is assigned

        -- In ill branch set, find the branch whose two ends are both normal bus. 
            -- Delete the branch. 
            -- In this situtation, the branch is ill and across two different interconnect regions. 
            -- However, the two end buses are unchangable due each bus is connected with the large network in each region.
        -- In ill branch set, find the branch whose two ends are one normal bus and one unlable bus.
            -- Assgin the unlable bus' interconnect region as the normal bus' interconnect region. 
            -- Assgin this branch's interconnnect region as the normal bus' interconnect region.
            -- In this sitution, one end of the branch is connected with the network of the region. The other end is a island. 
        -- In ill brnach set, find the branch whose two ends are both unlable buses.
            -- Delete the branch and both unlable buses.
            -- In this situtation, this branch is a island. 
        
"""

import pandas as pd

# please run this after running ercot_topology_validation


def get_zone(z_csv):
    """Generate a dictionary of zone using the zone.csv

    :param str z_csv: path of the zone.csv file
    :return: (*dict*) -- a dict mapping the name and interconnect to its ID.
    """

    zone = pd.read_csv(z_csv)

    zone_map = {}
    for i in range(len(zone)):
        tu = (zone["zone_name"][i], zone["interconnect"][i])
        zone_map[tu] = zone["zone_id"][i]
    return zone_map


def get_across_branch(branch, bus_dict):
    """Generate 2 dictionaries of branches and buses

    :param pandas.DataFrame branch: branch DataFrame from branch.csv
    :param dict bus_dict:a dict of buses' interconnect
    :return: (*dict*) -- branch_need_update, a dict of branches to be updated mapping to its 2 linked bus.
    :return: (*dict*) -- bus_acc, a dict of accurate buses mapping to their interconnect
    """
    branch_need_update = {}
    bus_acc = {}
    for br in branch.iloc:
        if bus_dict[br["from_bus_id"]] != bus_dict[br["to_bus_id"]]:
            branch_need_update[br["branch_id"]] = (br["from_bus_id"], br["to_bus_id"])
        else:
            if (
                br["from_bus_id"] in bus_acc
                and bus_acc[br["from_bus_id"]] != bus_dict[br["from_bus_id"]]
            ):
                print(br["from_bus_id"])
            else:
                bus_acc[br["from_bus_id"]] = bus_dict[br["from_bus_id"]]
            if (
                br["to_bus_id"] in bus_acc
                and bus_acc[br["to_bus_id"]] != bus_dict[br["to_bus_id"]]
            ):
                print(br["to_bus_id"])
            else:
                bus_acc[br["to_bus_id"]] = bus_dict[br["to_bus_id"]]
    return branch_need_update, bus_acc


def get_update_branch_bus(branch_need_update, bus_acc, zone_map, bus_state):
    """

    :param dict branch_need_update: branch dict , returned by :func: `get_across_branch`
    :param dict bus_acc:bus dict, returned by :func: `get_across_branch`
    :param dict zone_map:zone_id dict, returned by :func: `get_Zone`.
    :param dict bus_state:a dict mapping state to its ID.
    :return: (*dict*) -- branch_will_update, a dict of branches to be updated mapping to its interconnect.
    :return: (*dict*) -- bus_will_update, a dict of buses mapping to its new interconnect.
    :return: (*list*) -- bus_delete, a list of buses need to be deleted.
    :return: (*list*) -- br_delete, a list of branches need to be deleted.
    """
    bus_will_update = {}
    branch_will_update = {}

    br_delete = []
    bus_delete = []
    for br in branch_need_update:
        if branch_need_update[br][0] in bus_acc and (
            branch_need_update[br][1] in bus_acc
        ):
            # print(br,branch_need_update[br][0],branch_need_update[br][1])
            br_delete.append(br)

    for br in br_delete:
        del branch_need_update[br]

    for br in branch_need_update:
        if branch_need_update[br][0] in bus_acc or (
            branch_need_update[br][1] in bus_acc
        ):
            if branch_need_update[br][0] in bus_acc:
                if (
                    branch_need_update[br][1] in bus_will_update
                    and bus_will_update[branch_need_update[br][1]]
                    != bus_acc[branch_need_update[br][0]]
                ):
                    print(
                        br,
                        bus_acc[branch_need_update[br][0]],
                        bus_will_update[branch_need_update[br][1]],
                    )
                else:
                    if (
                        bus_state[branch_need_update[br][1]],
                        bus_acc[branch_need_update[br][0]],
                    ) in zone_map:
                        bus_will_update[branch_need_update[br][1]] = bus_acc[
                            branch_need_update[br][0]
                        ]
                        branch_will_update[br] = bus_acc[branch_need_update[br][0]]
                    else:
                        print(br, branch_need_update[br][1])
                        br_delete.append(br)
                        bus_delete.append(branch_need_update[br][1])

            elif branch_need_update[br][1] in bus_acc:
                if (
                    branch_need_update[br][0] in bus_will_update
                    and bus_will_update[branch_need_update[br][0]]
                    != bus_acc[branch_need_update[br][1]]
                ):
                    print(
                        br,
                        bus_acc[branch_need_update[br][1]],
                        bus_will_update[branch_need_update[br][0]],
                    )
                else:
                    if (
                        bus_state[branch_need_update[br][0]],
                        bus_acc[branch_need_update[br][1]],
                    ) in zone_map:
                        bus_will_update[branch_need_update[br][0]] = bus_acc[
                            branch_need_update[br][1]
                        ]
                        branch_will_update[br] = bus_acc[branch_need_update[br][1]]
                    else:
                        print(br, branch_need_update[br][0])
                        br_delete.append(br)
                        bus_delete.append(branch_need_update[br][0])

    for br in branch_will_update:
        del branch_need_update[br]

    for br in br_delete:
        if br in branch_need_update:
            del branch_need_update[br]

    for br in branch_need_update:
        br_delete.append(br)
        # bus_delete.append(branch_need_update[br][0])
        # bus_delete.append(branch_need_update[br][1])

    return bus_will_update, branch_will_update, br_delete, bus_delete


def update_sub(sub, bus_will_update, bus_delete, zone_map):
    """Update sub.csv

    :param pandas.DataFrame sub: substation DataFrame from sub.csv.
    :param dict bus_will_update: a dict of buses mapping to its new interconnect, returned by :func: `get_update_branch_bus`.
    :param list bus_delete: a list of buses need to be deleted, returned by :func: `get_update_branch_bus`.
    :param dict zone_map:zone_id dict, returned by :func: `get_Zone`.
    :return: (*pandas.DataFrame*) -- sub, final substation DataFrame.
    """
    for index, row in sub.iterrows():
        if row["sub_id"] in bus_will_update:
            sub.loc[index, "interconnect"] = bus_will_update[row["sub_id"]]
            print(sub.loc[index, "zone_id"])
            sub.loc[index, "zone_id"] = zone_map[
                (row["state"], bus_will_update[row["sub_id"]])
            ]
            print(sub.loc[index, "zone_id"])
            print(row["sub_id"], bus_will_update[row["sub_id"]])
    sub = sub[-sub.sub_id.isin(bus_delete)]
    return sub


def update_bus(bus, bus_will_update, bus_delete, zone_map):
    """Update bus.csv

    :param pandas.DataFrame bus: bus DataFrame from bus.csv.
    :param dict bus_will_update: a dict of buses mapping to its new interconnect, returned by :func: `get_update_branch_bus`.
    :param list bus_delete: a list of buses need to be deleted, returned by :func: `get_update_branch_bus`.
    :param dict zone_map:zone_id dict, returned by :func: `get_Zone`.
    :return: (*pandas.DataFrame*) -- bus, final bus DataFrame.
    """
    for index, row in bus.iterrows():
        if row["bus_id"] in bus_will_update:
            bus.loc[index, "interconnect"] = bus_will_update[row["bus_id"]]
            print(bus.loc[index, "zone_id"])
            bus.loc[index, "zone_id"] = zone_map[
                (row["state"], bus_will_update[row["bus_id"]])
            ]
            print(bus.loc[index, "zone_id"])
            print(row["bus_id"], bus_will_update[row["bus_id"]])
    bus = bus[-bus.bus_id.isin(bus_delete)]
    return bus


def update_bus2sub(bus2sub, bus_will_update, bus_delete):
    """Update bus2sub.csv

    :param pandas.DataFrame bus2sub: bus2sub DataFrame from bus2sub.csv.
    :param dict bus_will_update: a dict of buses mapping to its new interconnect, returned by :func: get_update_branch_bus().
    :param list bus_delete: a list of buses need to be deleted, returned by :func: get_update_branch_bus().
    :return: (*pandas.DataFrame*) -- bus2sub, final bus DataFrame.
    """
    for index, row in bus2sub.iterrows():
        if row["bus_id"] in bus_will_update:
            bus2sub.loc[index, "interconnect"] = bus_will_update[row["bus_id"]]
            # print(row['bus_id'],bus_will_update[row['bus_id']])
    bus2sub = bus2sub[-bus2sub.bus_id.isin(bus_delete)]
    return bus2sub


def update_branch(branch, branch_will_update, br_delete):
    """Update branch.csv

    :param pandas.DataFrame branch: branch DataFrame from bus2sub.csv.
    :param dict branch_will_update: a dict of branches to be updated mapping to its interconnect, returned by :func: `get_update_branch_bus`.
    :param list br_delete: a list of branches need to be deleted, returned by :func: `get_update_branch_bus()`
    :return: (*pandas.DataFrame*) -- branch, final branch DataFrame.
    """
    for index, row in branch.iterrows():
        if row["branch_id"] in branch_will_update:
            branch.loc[index, "interconnect"] = branch_will_update[row["branch_id"]]
            # print(row['branch_id'],branch_will_update[row['branch_id']])
    branch = branch[-branch.branch_id.isin(br_delete)]
    return branch


def bus_branch_validation():

    zone_map = get_zone("data/zone.csv")
    branch = pd.read_csv("output/branch.csv")
    bus = pd.read_csv("output/bus.csv")
    bus_dict = bus.set_index("bus_id")["interconnect"].to_dict()
    bus_state = bus.set_index("bus_id")["state"].to_dict()
    sub = pd.read_csv("output/sub.csv")
    bus2sub = pd.read_csv("output/bus2sub.csv")
    branch_need_update, bus_acc = get_across_branch(branch, bus_dict)
    bus_will_update, branch_will_update, br_delete, bus_delete = get_update_branch_bus(
        branch_need_update, bus_acc, zone_map, bus_state
    )
    bus = update_bus(bus, bus_will_update, bus_delete, zone_map)
    sub = update_sub(sub, bus_will_update, bus_delete, zone_map)
    bus2sub = update_bus2sub(bus2sub, bus_will_update, bus_delete)
    branch = update_branch(branch, branch_will_update, br_delete)
    branch.to_csv("output/branch.csv", index=False)
    bus.to_csv("output/bus.csv", index=False)
    bus2sub.to_csv("output/bus2sub.csv", index=False)
    sub.to_csv("output/sub.csv", index=False)


if __name__ == "__main__":
    bus_branch_validation()
