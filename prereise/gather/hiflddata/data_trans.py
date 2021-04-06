import json
import os.path
import zipfile
from collections import defaultdict

import networkx as nx
import pandas as pd
from haversine import Unit, haversine


def get_zone(z_csv):
    """Generate a dictionary of zone using the zone.csv

    :param str z_csv: path of the zone.csv file
    :return: (*dict*) -- a dict mapping the STATE to its ID.
    """

    zone = pd.read_csv(z_csv)
    # Create dictionary to store the mapping of states and codes
    return dict(zip(zone.STATE, zone.ID))


def clean(e_csv, zone_dic):
    """Clean data; remove substations which are outside the United States or not available.

    :param str e_csv: path of the HIFLD substation csv file
    :param dict zone_dic: zone dict as returned by :func:`get_zone`
    :return: (*pandas.DataFrame*) -- a pandas Dataframe storing the substations after dropping the invalid ones.
    """

    return pd.read_csv(e_csv).query(
        "STATE in @zone_dic and STATUS == 'IN SERVICE' and LINES != 0"
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
        candidate_coordinates = sub_name_dict.get(
            line["properties"]["SUB_1"]
        ) + sub_name_dict.get(line["properties"]["SUB_2"])

        sub1 = min(
            candidate_coordinates, key=lambda p: compute_geo_dist(p, start_coord)
        )
        sub2 = min(candidate_coordinates, key=lambda p: compute_geo_dist(p, end_coord))

        dist = compute_geo_dist(start_coord, end_coord)

        lines.append(
            [
                line_id,  # line id
                line_type,  # line type
                sub_by_coord_dict.get(sub1)[0],  # from substation id
                sub_by_coord_dict.get(sub1)[1],  # from substation name
                sub_by_coord_dict.get(sub2)[0],  # to substation id
                sub_by_coord_dict.get(sub2)[1],  # to substation name
                dist,  # distance between start point and end point of the line.
            ]
        )

        if sub1 == sub2:
            continue
        n_dict[sub1].append(sub2)
        n_dict[sub2].append(sub1)

    df_lines = pd.DataFrame(
        lines,
        columns=[
            "branch_id",
            "line_type",
            "from_bus_id",
            "from_bus_name",
            "to_bus_id",
            "to_bus_name",
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

    return haversine(sub1, sub2, Unit.MILES)


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

    return list(max(nx.connected_components(graph), key=len))


def init_kv(clean_data, max_value=1100, min_value=0):
    """Calculate the base_KV for each node based on MIN_VOLT and MAX_VOLT;
    Save the invalid substations as to be calculated later

    :param pandas.DataFrame clean_data: substation dataframe as returned by :func:`clean`
    :return: (*dict*) -- kv_dict, a dict of substation's base_kv value.
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


def get_neighbors(graph, node, depth=1):
    """Give a node, find its neighbors in given number depth

    :param networkx.Graph graph: Graph generated by :func:`GraphOfNet`
    :param tuple node: substation coordinate tuple
    :param int depth: number of hops that we are searching the neighbor substations
    :return: (*dict*) --  a dict mapping from depth to closest substations on that depth.
    """
    output = {}
    layers = dict(nx.bfs_successors(graph, source=node, depth_limit=depth))
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
            else:
                kv_dict[sub] = -999999


def set_sub(e_csv):
    """Generate the subs

    :param str E_csv: path of the HIFLD substation csv file
    :return: (*dict*) --  sub_by_coord_dict, a dict mapping from (x, y) to substation detail.
    :return: (*dict*) --  sub_name_dict, a dict mapping from substation name to its coordinate (x, y).
    """

    sub_by_coord_dict = {}
    sub_name_dict = defaultdict(list)
    raw_subs = pd.read_csv(e_csv)
    for _, row in raw_subs.iterrows():
        location = (row["LATITUDE"], row["LONGITUDE"])
        if location in sub_by_coord_dict:
            raise Exception(
                f"WARNING: substations coordinates conflict check: {location}"
            )
        sub_by_coord_dict[location] = (row["ID"], row["NAME"])
        sub_name_dict[row["NAME"]].append((row["LATITUDE"], row["LONGITUDE"]))
    return sub_by_coord_dict, sub_name_dict


def write_sub(clean_data, zone_dic):
    """Write the data to sub.csv as output

    :param pandas.DataFrame clean_data: substation dataframe as returned by :func:`clean`
    :param dict zone_dic: zone dict as returned by :func:`get_zone`
    """

    output = pd.DataFrame()
    output["sub_id"] = clean_data["ID"]
    output["sub_name"] = clean_data["NAME"]
    output["lat"] = clean_data["LATITUDE"]
    output["lon"] = clean_data["LONGITUDE"]
    output["zone_id"] = clean_data.apply(lambda x: zone_dic[x["STATE"]], axis=1)
    output["type"] = clean_data["TYPE"]
    output.to_csv("output/sub.csv", index=False)


def write_bus(clean_data, zone_dic, kv_dict):
    """Write the data to bus.csv as output

    :param pandas.DataFrame clean_data: substation dataframe as returned by :func:`clean`
    :param dict zone_dic: zone dict as returned by :func:`get_zone`
    :param dict kv_dict: substation KV dict
    """

    missing_sub, data = [], []
    for _, row in clean_data.iterrows():
        sub = (row["LATITUDE"], row["LONGITUDE"])
        if sub in kv_dict:
            data.append((row["ID"], 0, zone_dic[row["STATE"]], kv_dict[sub]))
        else:
            missing_sub.append(sub)

    output = pd.DataFrame(data, columns=["bus_id", "pd", "zone_id", "base_kv"])
    output.to_csv("output/bus.csv", index=False)

    print(
        "INFO: ",
        len(missing_sub),
        " substations excluded from the network. Some examples:",
    )
    print(missing_sub[:20])


def write_bus2sub(clean_data):
    """Write the data to bus2sub.csv as output

    :param pandas.DataFrame clean_data: substation dataframe as returned by :func:`clean`
    """

    output = pd.DataFrame()
    output["bus_id"] = clean_data["ID"]
    output["sub_id"] = clean_data["ID"]
    output.to_csv("output/bus2sub.csv", index=False)


def write_branch(lines):
    """Write the data to branch.csv as output

    :param list lines:  a list of lines as returned by :func:`neighbors`
    """

    lines.to_csv("output/branch.csv", index=False)


# Reactance Calculate 1
kv_xperunit_calculate_1 = (
    (69, 0.2293),
    (115, 0.1106),
    (230, 0.0567),
    (345, 0.0074),
    (500, 0.0001),
    (1100, 0.0001),
)

# Reactance Calculate 2
kv_xperunit_calculate_2 = (
    (69, 0.0096),
    (100, 0.0063),
    (115, 0.0039),
    (138, 0.0026),
    (161, 0.0021),
    (230, 0.0011),
    (345, 0.0005),
    (500, 0.0002),
    (765, 0.0001),
    (1100, 0.0001),
)

# RateA Calculate 3
kv_rate_a_calculate_3 = (
    (69, 86),
    (100, 181),
    (115, 239),
    (138, 382),
    (161, 446),
    (230, 797),
    (345, 1793),
    (500, 2598),
    (765, 5300),
    (1100, 5300),
)

# RateA Calculate 3
kv_sil_calculate_3 = (
    (69, 13),
    (100, 30),
    (115, 35),
    (138, 50),
    (161, 69),
    (230, 140),
    (345, 375),
    (500, 1000),
    (765, 2250),
    (1100, 2250),
)

# Reactance Calculate 4
kv_from_to_xperunit_calculate_4 = {
    (69, 165): 0.14242,
    (69, 138): 0.10895,
    (69, 161): 0.14943,
    (69, 230): 0.09538,
    (69, 345): 0.08896,
    (115, 161): 0.04516,
    (115, 230): 0.04299,
    (115, 345): 0.04020,
    (115, 500): 0.06182,
    (138, 161): 0.02818,
    (138, 230): 0.03679,
    (138, 345): 0.03889,
    (138, 500): 0.03279,
    (138, 765): 0.02284,
    (161, 230): 0.06539,
    (161, 345): 0.03293,
    (161, 500): 0.06978,
    (230, 345): 0.02085,
    (230, 500): 0.01846,
    (230, 765): 0.01616,
    (345, 500): 0.01974,
    (345, 765): 0.01625,
    (500, 765): 0.00436,
}


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
    :param int kv_from: KV of the substation1 at one end
    :param int kv_to: KV of the substation2 at the other end
    :param float dist: distance between the two substations
    :param int vol: transmission line voltage
    :return: (*float*) --  rateA value.
    """

    if line_type.startswith("DC"):
        # calculate 3 -> else
        for kv, sil in kv_rate_a_calculate_3:
            if vol <= kv:
                return pow(sil * 43.261 * dist, -0.6678)

    # line type is AC
    if kv_from == kv_to:
        if dist < 0.01:  # Phase shifter
            return 0.0
        else:  # AC Transmission Line
            # calculate 3
            if dist < 50:
                for kv, rate_a in kv_rate_a_calculate_3:
                    if vol <= kv:
                        return rate_a
            else:
                # (SIL*43.261*length)-0.6678
                for kv, sil in kv_sil_calculate_3:
                    if vol <= kv:
                        return pow(sil * 43.261 * dist, -0.6678)
    else:  # Transformer
        # calcuate 5: Use 700MVA or 800MVA for all 2-winding single transformers as a high-level approximation
        return 700.0


def get_bus_id_to_kv(clean_data, kv_dict):
    """Generating the dict mapping bus id to its KV

    :param pandas.DataFrame clean_data: substation dataframe as returned by :func:`clean`
    :param dict kv_dict: substation KV dict
    :return: (*dict*) -- a dict mapping the STATE to its ID after cleanup.
    """

    bus_id_to_kv = defaultdict(lambda: -999999)
    for _, row in clean_data.iterrows():
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
    for _, row in lines.iterrows():
        line_id, line_type, from_bus_id, to_bus_id, dist = (
            row["branch_id"],
            row["line_type"],
            row["from_bus_id"],
            row["to_bus_id"],
            row["length_in_mile"],
        )
        kv_from, kv_to = bus_id_to_kv[from_bus_id], bus_id_to_kv[to_bus_id]
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


def data_transform(e_csv, t_csv, z_csv):
    """Entry point to start the HIFLD parsing

    :param str e_csv: path of the HIFLD substation csv file
    :param str t_csv: path of the HIFLD transmission csv file
    :param str z_csv: path of the zone csv file
    """

    zone_dic = get_zone(z_csv)

    clean_data = clean(e_csv, zone_dic)

    sub_by_coord_dict, sub_name_dict = set_sub(e_csv)
    raw_lines = line_from_csv(t_csv)

    lines, n_dict = neighbors(sub_by_coord_dict, sub_name_dict)
    graph = graph_of_net(n_dict)
    print("Island Detection: number of nodes in graph = ", len(graph.nodes))
    print("Island Detection: max island size = ", len(get_max_island(graph)))
    kv_dict, to_cal = init_kv(clean_data)
    cal_kv(n_dict, graph, kv_dict, to_cal)
    bus_id_to_kv = get_bus_id_to_kv(clean_data, kv_dict)
    calculate_reactance_and_rate_a(bus_id_to_kv, lines, raw_lines)

    write_sub(clean_data, zone_dic)
    write_bus(clean_data, zone_dic, kv_dict)
    write_bus2sub(clean_data)
    write_branch(lines)


if __name__ == "__main__":
    data_transform(
        "data/Electric_Substations.csv",
        "data/Electric_Power_Transmission_Lines.csv",
        "data/zone.csv",
    )
