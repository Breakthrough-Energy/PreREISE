"""
Read data from Homeland Infrastructure Foundation-Level Data (HIFLD)  and Configuration Data
        --  HIFLD Data:  transmission line, substation
        --  Configuration Data:  zone.csv

Write data for grid simulation
        -- bus.csv  sub.csv bus2sub.csv branch.csv

Core Tasks
        -- 1 Electrcity grid topology population (EGTP)
        -- 2 Calcualte the BaseKV for each Bus/Substation (CBKV)
        -- 3 Assign U.S. Interconnection Region to each Bus/Substation (AIR2B)
        -- 4 Calculate power load for each substation  (CPD4S)
        -- 5 Calcluate transmission line paramaters RateA and X (CLPRAX)

Preprocess Tasks
        -- 1 Create Hashmaps for zones
            -- 1.1 Map zone name to Zone ID
            -- 1.2 Map (zone name, zone interconnection region)  to Zone ID
        -- 2 Clean substation data
            -- 2.1 remove states not in zone.csv
            -- 2.2 remove sustation without any lines
            -- 2.3 remove substation without countyFIPS
        -- 3 Create Hashmap for substation
            -- 3.1 Map geo location (latitude, longitude) to (substation ID, substation name, substation state, substation county)
            -- 3.2 Map substation name to location (latitude, longtitude)
        -- 4 Creat Hashmap for tramission line
            -- 4.1 Map transmission ID to raw parameters. (a row of data from HIFLD transmission line file)
        -- 5 Creat List/Hashmap for tranmssion line /Substation
            -- 5.1 List of clean tranmssion line datas
            -- 5.2 Map Substation ID to List of neighbor substations

Postprocess Tasks
        -- 1 remove islands
"""

import csv
import json
import os.path
import zipfile
from collections import defaultdict

import networkx as nx
import numpy as np
import pandas as pd
from powersimdata.utility.distance import haversine

from prereise.gather.hiflddata.load_dist import compute_load_dist
from prereise.gather.hiflddata.transmission_param import (
    kv_from_to_xperunit_calculate_4,
    kv_rate_a_calucate_3,
    kv_sil_calculate_3,
    kv_xperunit_calculate_1,
    kv_xperunit_calculate_2,
)


def get_zone(z_csv):
    """Generate a dictionary of zone using the zone.csv

    :param str z_csv: path of the zone.csv file
    :return: (*dict*) -- a dict mapping the STATE to its ID.
    """

    zone = pd.read_csv(z_csv)

    # Create dictionary to store the mapping of states and codes
    zone_dic = {}
    zone_dic1 = {}
    for i in range(len(zone)):
        tu = (zone["zone_name"][i], zone["interconnect"][i])
        zone_dic[zone["zone_name"][i]] = zone["zone_id"][i]
        zone_dic1[tu] = zone["zone_id"][i]
    return zone_dic, zone_dic1


West = ["WA", "OR", "CA", "NV", "AK", "ID", "UT", "AZ", "WY", "CO", "NM"]
Uncertain = ["MT", "SD", "TX"]


def get_region():
    region = {}
    csv_data = pd.read_csv("data/needs.csv")
    df = np.array(csv_data)
    needs = df.tolist()
    for pla in needs:
        name = str(pla[0]).upper()
        if name not in region:
            if pla[8][0:3] == "ERC":
                re = "Texas"
            elif pla[8][0:3] == "WEC":
                re = "Western"
            else:
                re = "Eastern"
            region[name] = re
    return region


def clean(e_csv, zone_dic):
    """Clean data; remove substations which are outside the United States or not available.
    :param str e_csv: path of the HIFLD substation csv file
    :param dict zone_dic: zone dict as returned by :func:`get_zone`
    :return: (*pandas.DataFrame*) -- a pandas Dataframe storing the substations after dropping the invalid ones.
    """
    return pd.read_csv(e_csv, dtype={"COUNTYFIPS": str}).query(
        "STATE in @zone_dic and LINES != 0"
    )


def neighbors(sub_by_coord_dict, sub_name_dict):
    """Create dict to store the neighbors of each substation based on transmission topology geojson from HIFLD
    :param dict sub_by_coord_dict: dict mapping the (x, y) to a substation (sub id and sub name)
    :param dict sub_name_dict: dict mapping the substation name to a list of (x, y)
    :return: (*list*) -- lines, a list of lines after the unambiguous substation name cleanup.
    :return: (*dict*) -- n_dict, a dict mapping the substation to its neighbor list.
    """

    n_dict = defaultdict(list)
    lines = []
    missing_lines = []
    if not os.path.isfile("data/unzip/Electric_Power_Transmission_Lines.geojson"):
        with zipfile.ZipFile(
            "data/Electric_Power_Transmission_Lines.geojson.zip", "r"
        ) as zip_ref:
            zip_ref.extractall("data/unzip")
    with open(
        "data/unzip/Electric_Power_Transmission_Lines.geojson", "r", encoding="utf8"
    ) as fp:
        data = json.load(fp)
    for i, line in enumerate(data["features"]):
        line_id = line["properties"]["ID"]
        line_type = line["properties"]["TYPE"]  # e.g. "AC; OVERHEAD"
        if (
            line["properties"]["SUB_1"] == "NOT AVAILABLE"
            or line["properties"]["SUB_2"] == "NOT AVAILABLE"
        ):
            # quite a few of NOT AVAILABLE scenarios in transmission rawdata
            print("INFO: sub1 or sub2 NOT AVAILABLE for transmission line: ", line)
            missing_lines.append(line)
            continue

        if (
            line["properties"]["SUB_1"] not in sub_name_dict
            or line["properties"]["SUB_2"] not in sub_name_dict
        ):
            # e.g., ID 201978 with SUB2 UNKNOWN202219, never shown in substation rawdata
            print(
                "INFO: sub1 or sub2 name not identified for transmission line: ", line
            )
            missing_lines.append(line)
            continue

        # line["geometry"]["coordinates"][0] gets a list of point on the transmission line
        # line["geometry"]["coordinates"][0][0] gets the start point(latitude, longitude) of the line
        # line["geometry"]["coordinates"][0][-1] gets the end point(latitude, longitude) of the line
        start_coord = (
            line["geometry"]["coordinates"][0][0][1],
            line["geometry"]["coordinates"][0][0][0],
        )
        end_coord = (
            line["geometry"]["coordinates"][0][-1][1],
            line["geometry"]["coordinates"][0][-1][0],
        )
        start_candidate_coordinates = sub_name_dict.get(line["properties"]["SUB_1"])
        end_candidate_coordinates = sub_name_dict.get(line["properties"]["SUB_2"])

        sub1 = min(
            start_candidate_coordinates, key=lambda p: compute_geo_dist(p, start_coord)
        )
        sub2 = min(
            end_candidate_coordinates, key=lambda p: compute_geo_dist(p, end_coord)
        )

        # If the distance between start_coord and sub1 is more than 100 miles (similar for end_coord and sub2),
        # we consider it is invalid matching. Those subs got removed during cleanup and could not be matched
        if (
            compute_geo_dist(sub1, start_coord) > 100
            or compute_geo_dist(sub2, end_coord) > 100
        ):
            print(
                "INFO: sub1 or sub2 name identified with wrong coordinates for transmission line: ",
                line,
            )
            missing_lines.append(line)
            continue

        dist = compute_geo_dist(start_coord, end_coord)

        if sub1 == sub2:
            # e.g., ID 300380 with SUB1 and SUB2 both HARRINGTON, both matched to the same sub
            print("INFO: sub1 and sub2 being same for transmission line: ", line)
            missing_lines.append(line)
            continue

        lines.append(
            [
                line_id,  # line id
                line_type,  # line type
                sub_by_coord_dict.get(sub1)[0],  # from substation id
                sub_by_coord_dict.get(sub1)[1],  # from substation name
                sub_by_coord_dict.get(sub1)[2],  # from substation state
                sub_by_coord_dict.get(sub1)[3],  # from substation county
                sub_by_coord_dict.get(sub2)[0],  # to substation id
                sub_by_coord_dict.get(sub2)[1],  # to substation name
                sub_by_coord_dict.get(sub2)[2],  # to substation state
                sub_by_coord_dict.get(sub2)[3],  # to substation county
                dist,  # distance between start point and end point of the line.
            ]
        )

        n_dict[sub1].append(sub2)
        n_dict[sub2].append(sub1)

    df_lines = pd.DataFrame(
        lines,
        columns=[
            "branch_id",
            "line_type",
            "from_bus_id",
            "from_bus_name",
            "from_bus_state",
            "from_bus_county",
            "to_bus_id",
            "to_bus_name",
            "to_bus_state",
            "to_bus_county",
            "length_in_mile",
        ],
    )
    return df_lines, n_dict


def line_from_csv(t_csv):
    """Create dict to store all the raw transmission line csv data

    :param str t_csv: path of the HIFLD transmission csv file
    :return: (*dict*) -- a dict mapping the transmission ID to its raw parameters.
    """

    raw_data = pd.read_csv(t_csv)
    raw_data["ID"] = raw_data["ID"].astype("str")
    raw_lines = raw_data.set_index("ID").to_dict()
    return raw_lines


def meter_to_mile(dist):
    """Calculate the mile given the distance in meter

    :param float dist: length of the distance between two substations
    :return: (*float*) -- distance in mile unit.
    """

    return dist / 1609.34


def compute_geo_dist(sub1, sub2):
    """Compute the haversine geo distance of two substations
    :param tuple sub1: (latitude, longitude) of substation1
    :param tuple sub2: (latitude, longitude) of substation2
    :return: (*float*) -- distance between two geo coordinates.
    """

    return haversine(sub1, sub2)


def graph_of_net(n_dict):
    """Create the graph for the HIFLD transmission network
    :param dict n_dict: dict of substation's neighbors as the edge inside the Graph
    :return: (*networkx.Graph*) -- Graph generated by networkx.
    """
    nodes = list(n_dict.keys())
    graph = nx.Graph()
    any(graph.add_node(node) for node in nodes)
    any(
        graph.add_edge(node, neighbor)
        for node, neighbors in n_dict.items()
        for neighbor in neighbors
    )
    return graph


def get_max_island(graph):
    """Report the largest connected island to understand the topo nature of the graph

    :param networkx.Graph G: Graph generated by :func:`GraphOfNet`
    :return: (*list*) -- list of nodes inside the largest island.
    """

    return set(max(nx.connected_components(graph), key=len))


def init_kv(clean_data, max_value=1100, min_value=0):
    """Calculate the base_KV for each node based on MIN_VOLT and MAX_VOLT;
    Save the invalid substations as to be calculated later

    :param pandas.DataFrame clean_data: substation dataframe as returned by :func:`Clean`
    :return: (*dict*) -- KV_dict, a dict of substation's baseKV value.
    :return: (*list*) -- to_cal, a list of substations to be calculated using neighbour search.
    """

    kv_dict = {}
    to_cal = []
    for _, row in clean_data.iterrows():
        min_vol = row["MIN_VOLT"]
        max_vol = row["MAX_VOLT"]
        if min_value < min_vol < max_value:
            if min_value < max_vol < max_value:
                base_kv = (max_vol + min_vol) / 2
            else:
                base_kv = min_vol
        else:
            if min_value < max_vol < max_value:
                base_kv = max_vol
            else:
                to_cal.append((row["LATITUDE"], row["LONGITUDE"]))
                continue
        kv_dict[(row["LATITUDE"], row["LONGITUDE"])] = base_kv
    return kv_dict, to_cal


def get_neighbors(g, node, depth=1):
    """Give a node, find its neighbors in given number depth

    :param networkx.Graph g: Graph generated by :func:`GraphOfNet`
    :param tuple node: substation coordinate tuple
    :param int depth: number of hops that we are searching the neighbor substations
    :return: (*dict*) --  a dict mapping from depth to closest substations on that depth.
    """
    output = {}
    layers = dict(nx.bfs_successors(g, source=node, depth_limit=depth))
    nodes = [node]
    for i in range(1, depth + 1):
        output[i] = []
        for x in nodes:
            output[i].extend(layers.get(x, []))
        nodes = output[i]
    return output


def cal_kv(n_dict, graph, kv_dict, to_cal):
    """Estimate missing substation's KV data using the neighbors average calculation
    :param dict n_dict: dict of substation's neighbors as returned by :func:`Neighbors`
    :param networkx.Graph g: Graph generated by :func:`GraphOfNet`
    :param dict kv_dict: dict of existing baseKV for each substation
    :param list to_cal: list of the substations to be calculate using average KV
    """

    for sub in to_cal:
        if sub not in n_dict:
            continue
        neighbors = get_neighbors(graph, sub, depth=5)
        for depth in range(1, 6):
            count = sum(1 for neighbor in neighbors[depth] if neighbor in kv_dict)
            if count > 0:
                sum_kv = sum(kv_dict[nei] for nei in neighbors[depth] if nei in kv_dict)
                kv_dict[sub] = sum_kv / count
                break


def set_sub(clean_data):
    """Generate the subs

    :param str E_csv: path of the HIFLD substation csv file
    :return: (*dict*) --  sub_by_coord_dict, a dict mapping from (x, y) to substation detail.
    :return: (*dict*) --  sub_name_dict, a dict mapping from substation name to its coordinate (x, y).
    """

    sub_by_coord_dict = {}
    sub_name_dict = {"sub": []}
    for index, row in clean_data.iterrows():
        location = (row["LATITUDE"], row["LONGITUDE"])
        if location in sub_by_coord_dict:
            raise Exception(
                f"WARNING: substations coordinates conflict check: {location}"
            )
        sub_by_coord_dict[location] = (
            row["ID"],
            row["NAME"],
            row["STATE"],
            row["COUNTY"],
        )
        if row["NAME"] not in sub_name_dict:
            sub_name_dict[row["NAME"]] = []
        sub_name_dict[row["NAME"]].append((row["LATITUDE"], row["LONGITUDE"]))
    return sub_by_coord_dict, sub_name_dict


def write_sub(clean_data, zone_dic, zone_dic1, region):
    """Write the data to sub.csv as output

    :param pandas.DataFrame clean_data: substation dataframe as returned by :func:`Clean`
    :param dict zone_dic: zone dict as returned by :func:`get_Zone`
    """
    tx_west = ["EL PASO", "HUDSPETH"]
    tx_east = [
        "BOWIE",
        "MORRIS",
        "CASS",
        "CAMP",
        "UPSHUR",
        "GREGG",
        "MARION",
        "HARRISON",
        "PANOLA",
        "SHELBY",
        "SAN AUGUSTINE",
        "SABINE",
        "JASPER",
        "NEWTON",
        "ORANGE",
        "JEFFERSON",
        "LIBERTY",
        "HARDIN",
        "TYLER",
        "POLK",
        "TRINITY",
        "WALKER",
        "SAN JACINTO",
        "DALLAM",
        "SHERMAN",
        "HANSFORD",
        "OCHLTREE" "LIPSCOMB",
        "HARTLEY",
        "MOORE",
        "HUTCHINSON",
        "HEMPHILL",
        "RANDALL",
        "DONLEY",
        "PARMER",
        "BAILEY",
        "LAMB",
        "HALE",
        "COCHRAN",
        "HOCKLEY",
        "LUBBOCK",
        "YOAKUM",
        "TERRY",
        "LYNN",
        "GAINES",
    ]

    sd_west = ["LAWRENCE", "BUTTE", "FALL RIVER"]
    # nm_east = ['CURRY', 'LEA', 'QUAY', 'ROOSEVELT', 'UNION']
    mt_east = [
        "CARTER",
        "CUSTER",
        "ROSEBUD",
        "PRAIRIE",
        "POWDER RIVER",
        "DANIELS",
        "MCCONE",
        "DAWSON",
        "RICHLAND",
        "FALLON",
        "GARFIELD",
        "ROOSEVELT",
        "PHILLIPS",
        "SHERIDAN",
        "VALLEY",
        "WIBAUX",
    ]
    sub = open("output/sub.csv", "w", newline="")
    csv_writer = csv.writer(sub)
    csv_writer.writerow(
        [
            "sub_id",
            "name",
            "zip",
            "lat",
            "lon",
            "interconnect",
            "zone_id",
            "type",
            "state",
        ]
    )
    sub_code = {}
    re_code = {}
    for index, row in clean_data.iterrows():
        if row["STATE"] in West:
            re = "Western"
        elif row["STATE"] in Uncertain:
            if row["STATE"] == "TX":
                if row["COUNTY"] in tx_west:
                    re = "Western"
                elif row["COUNTY"] in tx_east:
                    re = "Eastern"
                else:
                    re = "Texas"

            elif row["STATE"] == "SD":
                if row["COUNTY"] in sd_west:
                    re = "Western"
                else:
                    re = "Eastern"
            elif row["STATE"] == "MT":
                if row["COUNTY"] in mt_east:
                    re = "Eastern"
                else:
                    # code = zone_dic1[(row['STATE'],re)]
                    re = "Western"
        else:
            re = "Eastern"

        code = zone_dic1[(row["STATE"], re)]
        sub_code[row["ID"]] = code
        re_code[row["ID"]] = re
        csv_writer.writerow(
            [
                row["ID"],
                row["NAME"],
                row["ZIP"],
                row["LATITUDE"],
                row["LONGITUDE"],
                re,
                code,
                row["TYPE"],
                row["STATE"],
            ]
        )

    sub.close()

    return re_code, sub_code


def write_bus(clean_data, sub_code, re_code, kv_dict):
    """Write the data to bus.csv as output

    :param pandas.DataFrame clean_data: substation dataframe as returned by :func:`Clean`
    :param dict zone_dic: zone dict as returned by :func:`get_Zone`
    :param dict kv_dict: substation KV dict
    """

    with open("output/bus.csv", "w", newline="") as bus:
        csv_writer = csv.writer(bus)
        csv_writer.writerow(
            [
                "bus_id",
                "type",
                "Pd",
                "Qd",
                "Gs",
                "Bs",
                "zone_id",
                "Vm",
                "Va",
                "baseKV",
                "loss_zone",
                "Vmax",
                "Vmin",
                "lam_P",
                "lam_Q",
                "mu_Vmax",
                "mu_Vmin",
                "interconnect",
                "state",
            ]
        )
        missing_sub = []
        for index, row in clean_data.iterrows():
            sub = (row["LATITUDE"], row["LONGITUDE"])
            if sub in kv_dict:
                csv_writer.writerow(
                    [
                        row["ID"],
                        1,
                        round(row["Pd"], 3),
                        0.0,
                        0.0,
                        0.0,
                        sub_code[row["ID"]],
                        0.0,
                        0.0,
                        kv_dict[sub],
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        re_code[row["ID"]],
                        row["STATE"],
                    ]
                )
            else:
                missing_sub.append(sub)

    print(
        "INFO: ",
        len(missing_sub),
        " substations excluded from the network. Some examples:",
    )
    print(missing_sub[:20])


def write_bus2sub(clean_data, re_code):
    """Write the data to bus2sub.csv as output

    :param pandas.DataFrame clean_data: substation dataframe as returned by :func:`Clean`
    """

    with open("output/bus2sub.csv", "w", newline="") as bus2sub:
        csv_writer = csv.writer(bus2sub)
        csv_writer.writerow(["bus_id", "sub_id", "interconnect"])
        for index, row in clean_data.iterrows():
            csv_writer.writerow([row["ID"], row["ID"], re_code[row["ID"]]])


def write_branch(lines):
    """Write the data to branch.csv as output

    :param list lines:  a list of lines as returned by :func:`Neighbors`
    """
    branch = open("output/branch.csv", "w", newline="")
    phase = open("output/Phase Shifter.csv", "w", newline="")
    dc = open("output/dcline.csv", "w", newline="")

    csv_writer = csv.writer(branch)
    csv_writer1 = csv.writer(phase)
    csv_writer2 = csv.writer(dc)
    csv_writer.writerow(
        [
            "branch_id",
            "from_bus_id",
            "to_bus_id",
            "r",
            "x",
            "b",
            "rateA",
            "rateB",
            "rateC",
            "ratio",
            "angle",
            "status",
            "angmin",
            "angmax",
            "Pf",
            "Qf",
            "Qt",
            "mu_Sf",
            "mu_St",
            "mu_angmin",
            "mu_angmax",
            "branch_device_type",
            "interconnect",
        ]
    )
    csv_writer1.writerow(
        [
            "branch_id",
            "from_bus_id",
            "to_bus_id",
            "r",
            "x",
            "b",
            "rateA",
            "rateB",
            "rateC",
            "ratio",
            "angle",
            "status",
            "angmin",
            "angmax",
            "Pf",
            "Qf",
            "Qt",
            "mu_Sf",
            "mu_St",
            "mu_angmin",
            "mu_angmax",
            "branch_device_type",
            "interconnect",
        ]
    )
    csv_writer2.writerow(
        [
            "dcline_id",
            "from_bus_id",
            "to_bus_id",
            "status",
            "Pf",
            "Pt",
            "Qf",
            "Qt",
            "Vf",
            "Vt",
            "Pmin",
            "Pmax",
            "QminF",
            "QmaxF",
            "QminT",
            "QmaxT",
            "loss0",
            "loss1",
            "muPmin",
            "muPmax",
            "muQminF",
            "muQmaxF",
            "from_interconnect",
            "to_interconnect",
        ]
    )
    bus_pd = pd.read_csv("output/bus.csv")
    bus_dict = {}
    for bus in bus_pd.iloc():
        bus_dict[bus["bus_id"]] = bus["interconnect"]
    for _, row in lines.iterrows():
        if row["line_type"] == "DC":
            from_connect = bus_dict[row["from_bus_id"]]
            to_connect = bus_dict[row["to_bus_id"]]
            csv_writer2.writerow(
                [
                    row["branch_id"],
                    row["from_bus_id"],
                    row["to_bus_id"],
                    1,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    -200,
                    200,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    from_connect,
                    to_connect,
                ]
            )
        else:
            csv_writer.writerow(
                [
                    row["branch_id"],
                    row["from_bus_id"],
                    row["to_bus_id"],
                    0.0,
                    row["reactance"],
                    0.0,
                    row["rateA"],
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    row["line_type"],
                    row["interconnect"],
                ]
            )
    branch.close()
    phase.close()
    dc.close()


"""
        elif row['line_type'] == 'Phase Shifter':
            csv_writer1.writerow(
                [
                    row["branch_id"],
                    row["from_bus_id"],
                    row["to_bus_id"],
                    0.0,
                    row["reactance"],
                    0.0,
                    row["rateA"],
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    row["line_type"],
                    row["interconnect"]
                ])
"""


def compute_reactance_and_type(line_type, kv_from, kv_to, dist, vol):
    """Compute the reactance based on the type of each transmission line
    :param str line_type: type of the transmission line between two substations
    :param int kv_from: KV of the substation1 at one end
    :param int kv_to: KV of the substation2 at the other end
    :param float dist: distance between the two substations
    :param int vol: transmission line voltage
    :return: (*float*) --  reactance value.
    :return: (*str*) --  line type.
    """

    if line_type.startswith("DC"):
        return 0.0, "DC"

    # line type is AC
    if kv_from == kv_to:
        if dist < 0.01:  # Phase Shifter
            # calculate 1
            for kv, x in kv_xperunit_calculate_1:
                if vol <= kv:
                    return x * dist, "Phase Shifter"
        elif (
            dist < 0.031
        ):  # If two are within 0.031 mile (~50 meters) range, they are in the same substation
            return (
                kv_from_to_xperunit_calculate_4.get((kv_from, kv_to), 0.00436) * dist,
                "Line",
            )
        else:  # AC Transmission Line
            # calculate 2
            for kv, x in kv_xperunit_calculate_2:
                if vol <= kv:
                    return x * dist, "Line"
    else:  # Transformer
        # calculate 4
        x = kv_from_to_xperunit_calculate_4.get((kv_from, kv_to), 0.00436)
        return x * dist, "Transformer"


def compute_rate_a(line_type, kv_from, kv_to, dist, vol):
    """Compute the rateA based on the type of each transmission line

    :param str line_type: type of the transmission line between two substations
    :param int KV_from: KV of the substation1 at one end
    :param int KV_to: KV of the substation2 at the other end
    :param float dist: distance between the two substations
    :param int vol: transmission line voltage
    :return: (*float*) --  rateA value.
    """

    if line_type.startswith("DC"):
        # initial setup for DC
        return 200
    elif (
        dist < 0.031
    ):  # If two are within 0.031 mile (~50 meters) range, they are in the same substation
        return 1793.0
    # line type is AC
    if kv_from == kv_to:
        if dist < 0.01:  # Phase shifter
            return 0.0
        else:  # AC Transmission Line
            # calculate 3
            if dist < 50:
                for kv, rate_a in kv_rate_a_calucate_3:
                    if vol <= kv:
                        return rate_a
            else:
                # SIL*43.261*(length^-0.6678)
                for kv, sil in kv_sil_calculate_3:
                    if vol <= kv:
                        return sil * 43.261 * pow(dist, -0.6678)
    else:  # Transformer
        # calcuate 5: Use 700MVA or 800MVA for all 2-winding single transformers as a high-level approximation
        return 700.0


def get_bus_id_to_kv(clean_data, kv_dict):
    """Generating the dict mapping bus id to its KV

    :param pandas.DataFrame clean_data: substation dataframe as returned by :func:`Clean`
    :param dict kv_dict: substation KV dict
    :return: (*dict*) -- a dict mapping the STATE to its ID after cleanup.
    """

    bus_id_to_kv = {}
    for index, row in clean_data.iterrows():
        sub = (row["LATITUDE"], row["LONGITUDE"])
        if sub in kv_dict:
            bus_id_to_kv[row["ID"]] = kv_dict[sub]
    return bus_id_to_kv


def calculate_reactance_and_rate_a(bus_id_to_kv, lines, raw_lines):
    """Preprocessing before calculating the reactance and rateA for each line

    :param dict bus_id_to_kv: dict mapping bus id to its KV
    :param list lines: list of all the lines after the neighbor cleanup
    :param list raw_lines: dict of raw transmission line data as returned by :func:`lineFromCSV`
    """

    line_types, rateas, reactances = [], [], []
    lines = lines[lines["from_bus_id"].isin(bus_id_to_kv.keys())]
    lines = lines[lines["to_bus_id"].isin(bus_id_to_kv.keys())]
    node_id_set = set()
    for _, row in lines.iterrows():
        line_id, line_type, from_bus_id, to_bus_id, dist = (
            row["branch_id"],
            row["line_type"],
            row["from_bus_id"],
            row["to_bus_id"],
            row["length_in_mile"],
        )
        kv_from, kv_to = bus_id_to_kv[from_bus_id], bus_id_to_kv[to_bus_id]
        node_id_set.add(from_bus_id)
        node_id_set.add(to_bus_id)
        vol = raw_lines["VOLTAGE"][line_id]
        reactance, type = compute_reactance_and_type(
            line_type, kv_from, kv_to, dist, vol
        )

        rate_a = compute_rate_a(line_type, kv_from, kv_to, dist, vol)
        line_types.append(type)
        rateas.append(rate_a)
        reactances.append(reactance)
    lines["line_type"] = line_types
    lines["reactance"] = reactances
    lines["rateA"] = rateas
    return lines, node_id_set


def data_transform(e_csv, t_csv, z_csv):
    """Entry point to start the HIFLD parsing

    :param str e_csv: path of the HIFLD substation csv file
    :param str t_csv: path of the HIFLD transmission csv file
    :param str z_csv: path of the zone csv file
    """

    zone_dic, zone_dic1 = get_zone(z_csv)

    clean_data = clean(e_csv, zone_dic)

    sub_by_coord_dict, sub_name_dict = set_sub(clean_data)
    raw_lines = line_from_csv(t_csv)

    lines, n_dict = neighbors(sub_by_coord_dict, sub_name_dict)
    graph = graph_of_net(n_dict)
    max_island_set = get_max_island(graph)
    clean_data = clean_data[
        clean_data[["LATITUDE", "LONGITUDE"]].apply(tuple, 1).isin(max_island_set)
    ]
    print("Island Detection: number of nodes in graph = ", len(graph.nodes))
    print("Island Detection: max island size = ", len(max_island_set))
    kv_dict, to_cal = init_kv(clean_data)
    cal_kv(n_dict, graph, kv_dict, to_cal)
    clean_data = compute_load_dist(clean_data, kv_dict)

    bus_id_to_kv = get_bus_id_to_kv(clean_data, kv_dict)
    lines, node_id_set = calculate_reactance_and_rate_a(bus_id_to_kv, lines, raw_lines)
    clean_data = clean_data[clean_data["ID"].isin(node_id_set)]

    region = get_region()

    re_code, sub_code = write_sub(clean_data, zone_dic, zone_dic1, region)
    write_bus(clean_data, sub_code, re_code, kv_dict)
    write_bus2sub(clean_data, re_code)
    lines["interconnect"] = lines.apply(
        lambda row: re_code.get(row["from_bus_id"]), axis=1
    )
    write_branch(lines)


if __name__ == "__main__":
    data_transform(
        "data/Electric_Substations.csv",
        "data/Electric_Power_Transmission_Lines.csv",
        "data/zone.csv",
    )
