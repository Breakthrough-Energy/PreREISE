#!/usr/bin/env python
# coding: utf-8


import pandas as pd
import networkx as nx
import csv
import json
import os.path
import zipfile
from haversine import haversine, Unit
from collections import defaultdict


Max_Value = 3000
Min_Value = 0
coord_precision = '.9f'
default_base_kv = -999999.0

def get_Zone(Z_csv):
    zone=pd.read_csv(Z_csv)

    # Create dictionary to store the mapping of states and codes
    zone_dic={}
    for i in range(len(zone)):
        zone_dic[zone['STATE'][i]]=zone['ID'][i]
    return zone_dic


# Clean data; throw substations which are outside the United States and not available.
def Clean(E_csv, zone_dic):
    csv_data = pd.read_csv(E_csv)
    Num_sub = len(csv_data)
    row_indexs = []
    for i in range(Num_sub):
        if((csv_data['STATE'][i] not in zone_dic) or (csv_data['STATUS'][i] != 'IN SERVICE') or (csv_data['LINES'][i] == 0)):
            row_indexs.append(i)
    clean_data = csv_data.drop(labels = row_indexs)
    return clean_data



#Create dictionary to store neighbors of each sub
def Neighbors(sub_by_coord_dict, sub_name_dict, raw_lines):
    N_dict = {}
    nodes = []
    lines = []
    missinglines = []
    if not os.path.isfile('data/unzip/Electric_Power_Transmission_Lines.geojson'):
        with zipfile.ZipFile('data/Electric_Power_Transmission_Lines.geojson.zip', 'r') as zip_ref:
            zip_ref.extractall('data/unzip')
    with open('data/unzip/Electric_Power_Transmission_Lines.geojson','r',encoding='utf8') as fp:
        data = json.load(fp)
    for i in range(len(data['features'])):
        line = data['features'][i]
        line_id = line['properties']['ID']
        line_type = line['properties']['TYPE'] # e.g. "AC; OVERHEAD"
        if line['properties']['SUB_1'] == 'NOT AVAILABLE' or line['properties']['SUB_2'] == 'NOT AVAILABLE':
            # quite a few of NOT AVAILABLE scenarios in transmission rawdata
            print("INFO: sub1 or sub2 NOT AVAILABLE for transmission line: ", line)
            missinglines.append(line)
            continue

        if line['properties']['SUB_1'] not in sub_name_dict or line['properties']['SUB_2'] not in sub_name_dict:
            # e.g., ID 201978 with SUB2 UNKNOWN202219, never shown in substation rawdata
            print("INFO: sub1 or sub2 name not identified for transmission line: ", line)
            missinglines.append(line)
            continue

        start_coord = (line['geometry']['coordinates'][0][0][1], line['geometry']['coordinates'][0][0][0])
        end_coord = (line['geometry']['coordinates'][0][-1][1], line['geometry']['coordinates'][0][-1][0])
        candidate_coordinates = sub_name_dict.get(line['properties']['SUB_1']) + sub_name_dict.get(line['properties']['SUB_2'])

        sub1 = min(candidate_coordinates, key=lambda p: computeGeoDist(p, start_coord))
        sub2 = min(candidate_coordinates, key=lambda p: computeGeoDist(p, end_coord))

        # dist = meter2Mile(raw_lines['SHAPE_Length'][line_id])
        dist = computeGeoDist(start_coord, end_coord)
        # vol = raw_lines['VOLTAGE'][line_id]
        # reactance = computeReactance(line_type, dist, vol)
        # rateA = computeRateA(line_type, vol)
        lines.append([line_id, line_type, sub_by_coord_dict.get(sub1)[0], sub_by_coord_dict.get(sub1)[1], sub_by_coord_dict.get(sub2)[0], sub_by_coord_dict.get(sub2)[1], dist])

        if (sub1 == sub2):
            continue
        if (sub1 in N_dict):
            N_dict[sub1].append(sub2)
        else:
            nodes.append(sub1)
            N_dict[sub1] = [sub2]
        if (sub2 in N_dict):
            N_dict[sub2].append(sub1)
        else:
            nodes.append(sub2)
            N_dict[sub2] = [sub1]
    return lines, nodes, N_dict


def lineFromCSV(T_csv):
    raw_data = pd.read_csv(T_csv)
    raw_data['ID'] = raw_data['ID'].astype('str')
    raw_lines = raw_data.set_index('ID').to_dict()
    return raw_lines

def meter2Mile(dist):
    return dist/1609.34

def computeGeoDist(sub1, sub2):
    return haversine(sub1, sub2, Unit.MILES)

#create the graph for our Power Network
def GraphOfNet(nodes, N_dict):
    G = nx.Graph()
    for node in nodes:
        G.add_node(node)

    for key in N_dict:
        for value in N_dict[key]:
            G.add_edge(key, value)

    return G

#Find the biggest islands, only used to test at present
def GetMaxIsland(G):
    Max_nodeSet = []
    Max_size = 0
    #list1 = []
    num = 0
    for c in nx.connected_components(G):
        num = num +1
        nodeSet = G.subgraph(c).nodes()
        size = len(nodeSet)
        #list1.append(size)
        if(size > Max_size):
            Max_nodeSet = nodeSet
            Max_size = size
    #list1.sort(reverse=True)
    return Max_nodeSet

#Calculate the base_KV for each node, save the nodes to be calculated

def InitKV(clean_data):
    KV_dict = {}
    to_cal = []
    Max_Value = 3000
    Min_Value = 0
    for index, row in clean_data.iterrows():
        base_KV = default_base_kv
        Min_Vol = row['MIN_VOLT']
        Max_Vol = row['MAX_VOLT']
        if (Min_Vol >= Max_Value or Min_Vol <= Min_Value):
            if(Max_Vol < Max_Value and Max_Vol > Min_Value):
                base_KV = Max_Vol
            else:
                to_cal.append((row['LATITUDE'], row['LONGITUDE']))
                continue
        else:
            if (Max_Vol < Max_Value and Max_Vol > Min_Value):
                base_KV = (Max_Vol + Min_Vol)/2
            else:
                base_KV = Min_Vol
        KV_dict[(row['LATITUDE'], row['LONGITUDE'])] = base_KV
    return KV_dict, to_cal

# Give a node, find its neighbors in 5 iteration

def get_neigbors(g, node, depth=1):
    output = {}
    layers = dict(nx.bfs_successors(g, source=node, depth_limit=depth))
    nodes = [node]
    for i in range(1,depth+1):
        output[i] = []
        for x in nodes:
            output[i].extend(layers.get(x,[]))
        nodes = output[i]
    return output

# Estimate KV using neighbors

def Cal_KV(N_dict,G,KV_dict,to_cal):
    for sub in to_cal:
        if (sub not in N_dict):
            continue
        neigh = get_neigbors(G, sub, depth=5)
        temp_KV = 0
        num = 0
        for i in range(1, 6):
            for nei in neigh[i]:
                if (nei in KV_dict):
                    temp_KV = temp_KV + KV_dict[nei]
                    num = num + 1
            if (num > 0):
                KV_dict[sub] = temp_KV / num
                continue
            else:
                KV_dict[sub] = -999999
    return KV_dict


def Set_Sub(E_csv):
    sub_by_coord_dict = {}
    sub_name_dict = {"sub": []}
    raw_subs = pd.read_csv(E_csv)
    for index, row in raw_subs.iterrows():
        location = (row['LATITUDE'], row['LONGITUDE'])
        if location in sub_by_coord_dict:
            print("WARNING: substations coordinates conflict check:", location)
        sub_by_coord_dict[location] = (row['ID'], row['NAME'])
        if row['NAME'] not in sub_name_dict:
            sub_name_dict[row['NAME']] = []
        sub_name_dict[row['NAME']].append((row['LATITUDE'], row['LONGITUDE']))
    return sub_by_coord_dict, sub_name_dict

# Write sub.csv
def Write_sub(clean_data,zone_dic):
    sub = open('output/sub.csv','w',newline='')
    csv_writer = csv.writer(sub)
    csv_writer.writerow(["sub_id","sub_name","lat","lon","zone_id","type"])
    for index, row in clean_data.iterrows():
        csv_writer.writerow([row['ID'],row['NAME'],row['LATITUDE'],row['LONGITUDE'],zone_dic[row['STATE']],row['TYPE']])
    sub.close()


#Write bus.csv
def Write_Bus(clean_data, zone_dic, KV_dict):
    bus = open('output/bus.csv', 'w', newline='')
    csv_writer = csv.writer(bus)
    csv_writer.writerow(["Bus_id", "PD", "Zone_id", "base_KV"])
    missingSub = []
    for index, row in clean_data.iterrows():
        sub = (row['LATITUDE'], row['LONGITUDE'])
        if (sub in KV_dict):
            csv_writer.writerow([row['ID'], 0, zone_dic[row['STATE']], KV_dict[sub]])
        else:
            missingSub.append(sub)
    bus.close()
    print("INFO: ", len(missingSub), " substations excluded from the network. Some examples:")
    print(missingSub[:20])


#Write bus2sub.csv
def Write_bus2sub(clean_data):
    bus2sub = open('output/bus2sub.csv','w',newline='')
    csv_writer = csv.writer(bus2sub)
    csv_writer.writerow(["Bus_id","sub_id"])
    for index, row in clean_data.iterrows():
        csv_writer.writerow([row['ID'],row['ID']])
    bus2sub.close()


#Write branch.csv
def Write_branch(lines):
    branch = open('output/branch.csv', 'w', newline='')
    csv_writer = csv.writer(branch)
    csv_writer.writerow(['branch_id', 'line_type', 'from_bus_id', 'from_bus_name', 'to_bus_id', 'to_bus_name', 'length_in_mile', 'reactance', 'rateA'])
    csv_writer.writerows(lines)
    branch.close()

# Reactance Calculate 1
kv_xperunit_calculate_1 = (
    (69, 0.2293),
    (115, 0.1106),
    (230, 0.0567),
    (345, 0.0074),
    (500, 0.0001),
    (2147483647, 0.0001)
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
    (2147483647, 0.0001)
)

# RateA Calculate 3
kv_rate_A_calucate_3 = (
    (69, 86),
    (100, 181),
    (115, 239),
    (138, 382),
    (161, 446),
    (230, 797),
    (345, 1793),
    (500, 2598),
    (765, 5300),
    (2147483647, 5300)
)

# RateA Calculate 3
kv_sil_calucate_3 = (
    (69, 13),
    (100, 30),
    (115, 35),
    (138, 50),
    (161, 69),
    (230, 140),
    (345, 375),
    (500, 1000),
    (765, 2250),
    (2147483647, 2250)
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

def computeReactanceAndType(line_type, KV_from, KV_to, dist, vol):
    if line_type.startswith('DC'):
        return 0.0, 'DC'

    # line type is AC
    if KV_from == KV_to:
        if dist < 0.01: # Phase Shifter
            # calculate 1
            for kv, x in kv_xperunit_calculate_1:
                if vol <= kv:
                    return x * dist, 'Phase Shifter'
        else: # AC Transmission Line
            # calculate 2
            for kv, x in kv_xperunit_calculate_2:
                if vol <= kv:
                    return x * dist, 'Line'
    else: # Transformer
        # calculate 4
        x = kv_from_to_xperunit_calculate_4.get((KV_from, KV_to), 0.00436)
        return x * dist, 'Transformer'


def computeRateA(line_type, KV_from, KV_to, dist, vol):
    if line_type.startswith('DC'):
        # calculate 3 -> else
        for kv, sil in kv_rate_A_calucate_3:
            if vol <= kv:
                return pow(sil * 43.261 * dist, -0.6678)

    # line type is AC
    if KV_from == KV_to:
        if dist < 0.01: # Phase shifter
            return 0.0
        else: # AC Transmission Line
            # calculate 3
            if dist < 50:
                for kv, rateA in kv_rate_A_calucate_3:
                    if vol <= kv:
                        return rateA
            else:
                # (SIL*43.261*length)-0.6678
                for kv, sil in kv_rate_A_calucate_3:
                    if vol <= kv:
                        return pow(sil * 43.261 * dist, -0.6678)
    else: # Transformer
        # calcuate 5: Use 700MVA or 800MVA for all 2-winding single transformers as a high-level approximation
        return 700.0


def get_bus_id_to_KV(clean_data, KV_dict):
    bus_id_to_KV = defaultdict(lambda: default_base_kv)
    for index, row in clean_data.iterrows():
        sub = (row['LATITUDE'], row['LONGITUDE'])
        if sub in KV_dict:
            bus_id_to_KV[row['ID']] = KV_dict[sub]
    return bus_id_to_KV


def calculate_reactance_and_rateA(bus_id_to_kv, lines, raw_lines):
    for line in lines:
        line_id, line_type, from_bus_id, to_bus_id, dist = line[0], line[1], line[2], line[4], line[-1]
        KV_from, KV_to = bus_id_to_kv[from_bus_id], bus_id_to_kv[to_bus_id]
        vol = raw_lines['VOLTAGE'][line_id]
        reactance, type = computeReactanceAndType(line_type, KV_from, KV_to, dist, vol)
        rateA = computeRateA(line_type, KV_from, KV_to, dist, vol)
        line[1] = type
        line.append(reactance)
        line.append(rateA)


def DataTransform(E_csv, T_csv, Z_csv):

    zone_dic = get_Zone(Z_csv)

    clean_data = Clean(E_csv, zone_dic)

    sub_by_coord_dict, sub_name_dict = Set_Sub(E_csv)
    raw_lines = lineFromCSV(T_csv)

    lines, nodes, N_dict = Neighbors(sub_by_coord_dict, sub_name_dict, raw_lines)
    G = GraphOfNet(nodes, N_dict)
    print("Island Detection: number of nodes in graph = ", len(G.nodes))
    print("Island Detection: max island size = ", len(GetMaxIsland(G)))
    KV_dict, to_cal= InitKV(clean_data)
    KV_dict = Cal_KV(N_dict,G, KV_dict, to_cal)
    bus_id_to_kv = get_bus_id_to_KV(clean_data, KV_dict)
    calculate_reactance_and_rateA(bus_id_to_kv, lines, raw_lines)

    Write_sub(clean_data, zone_dic)
    Write_Bus(clean_data, zone_dic, KV_dict)
    Write_bus2sub(clean_data)
    Write_branch(lines)

if __name__ == '__main__':
    DataTransform("data/Electric_Substations.csv", "data/Electric_Power_Transmission_Lines.csv", "data/zone.csv")

