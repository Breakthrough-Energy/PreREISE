import csv
import math
import numpy as np
import pandas as pd
from geopy.distance import geodesic

from data_trans import Clean, get_Zone

coord_precision = ".9f"

West = ['WA','OR','CA','NV','AK','ID','UT','AZ','WY','CO','NM']
Uncertain = ['MT','SD','TX']


def get_Zone(Z_csv):
    zone = pd.read_csv(Z_csv)

    # Create dictionary to store the mapping of states and codes
    zone_dic={}
    for i in range(len(zone)):
        zone_dic[zone["zone_name"][i]] = zone["zone_id"][i]
    return zone_dic


def Clean(E_csv,zone_dic):
    csv_data = pd.read_csv(E_csv)
    Num_sub = len(csv_data)
    row_indexs = []
    for i in range(Num_sub):
        if((csv_data['STATE'][i] not in zone_dic) or (csv_data['STATUS'][i] != 'IN SERVICE') or (csv_data['LINES'][i] == 0)):
            row_indexs.append(i)
    clean_data = csv_data.drop(labels = row_indexs)
    return clean_data

def Clean_p(P_csv):
    csv_data = pd.read_csv(P_csv)
    Num_sub = len(csv_data)
    row_indexs = []
    for i in range(Num_sub):
        if csv_data["STATUS"][i] != "OP":
            row_indexs.append(i)
    clean_data = csv_data.drop(labels=row_indexs)
    return clean_data


def LocOfsub(clean_data):
    """Get the latitude and longitude of substations, and the substations in the area of each zip code

    :param dict clean_data:  a dict of substations as returned by :func:`data_trans.Clean`
    :return: (*dict*) -- LocOfsub_dict, dict mapping the geo coordinate (x,y) to substations.
    :return: (*dict*) -- ZipOfsub_dict, dict mapping the zip code to a group of substations.
    """

    LocOfsub_dict = {}
    ZipOfsub_dict = {}
    for index, row in clean_data.iterrows():
        loc = (
            format(row["LATITUDE"], coord_precision),
            format(row["LONGITUDE"], coord_precision),
        )
        sub = row["ID"]
        zi = row["ZIP"]
        LocOfsub_dict[sub] = loc
        if zi in ZipOfsub_dict:
            list1 = ZipOfsub_dict[zi]
            list1.append(sub)
            ZipOfsub_dict[zi] = list1
        else:
            list1 = [sub]
            ZipOfsub_dict[zi] = list1
    return LocOfsub_dict, ZipOfsub_dict


def Cal_P(G_csv):
    """Calculate the Pmin for each plant

    :param dict G_csv: path of the EIA generator profile csv file
    :return: (*list*) -- a list of Pmin for the plants.
    """

    Pmin = {}
    csv_data = pd.read_csv(G_csv)
    for index, row in csv_data.iterrows():
        tu = (str(row["Plant Name"]).upper(),row['Energy Source 1'])
        Pmin[tu] = row["Minimum Load (MW)"]
    return Pmin


def Loc_of_plant():
    """Get the latitude and longitude of plants

    :return: (*list*) -- a list of power plants' geo coordinates.
    """

    loc_of_plant = {}
    csv_data = pd.read_csv("data/Power_Plants.csv")
    for index, row in csv_data.iterrows():
        loc = (
            format(row["LATITUDE"], coord_precision),
            format(row["LONGITUDE"], coord_precision),
        )
        loc_of_plant[row["NAME"]] = loc
    return loc_of_plant

def getCostCurve():
    points = {}
    csv_data = pd.read_csv("data/needs.csv")
    df = np.array(csv_data)
    cost = df.tolist()
    for pla in cost:
        name = (str(pla[0]).upper(), pla[4])
        points[name] = int(pla[13])
    return points

def getCostCurve2():
    curve = {}
    csv_data = pd.read_csv("data/curve.csv")
    df = np.array(csv_data)
    cost = df.tolist()
    for pla in cost:
        name = pla[0]
        curve[name] = (pla[1],pla[2],pla[3])
    return curve

def Getregion():
    region = {}
    csv_data = pd.read_csv("data/needs.csv")
    df = np.array(csv_data)
    needs = df.tolist()
    for pla in needs:
        name = (str(pla[0]).upper(), pla[4])
        if (name not in region):
            if(pla[8][0:3] == 'ERC'):
                re = 'Texas'
            elif(pla[8][0:3] == 'WEC'):
                re = 'Western'
            else:
                re = 'Eastern'
            region[name] = re
    return region

def Plant_agg(clean_data, ZipOfsub_dict, loc_of_plant, LocOfsub_dict, Pmin, region, points):
    """Aggregate the plant by zip code and build the plant dict with geo-based aggregation

    :return: (*dict*) -- a dict for power plant after aggregation
    """

    plant_dict = {}
    storage = open('output/storage.csv','w',newline="")
    csv_writer = csv.writer(storage)
    csv_writer.writerow(
            [
                'Storage_name',
                'Type',
                'SOC_max',
                'SOC_min',
                'Pchr_max',
                'Pdis_max',
                'Charge Efficiency',
                'Discharge Efficiency',
                'Loss Factor',
                'Terminal Max',
                'Terminal Min',
                'SOC_intial'
            ])
    sto = ['BATTERIES', 'NATURAL GAS WITH COMPRESSED AIR STORAGE','FLYWHEELS']
    sto_dict = {
                'BATTERIES' :0.95,
                'NATURAL GAS WITH COMPRESSED AIR STORAGE':0.50,
                'FLYWHEELS':0.90
                }
                
    for index, row in clean_data.iterrows():
        tu = (row["PLANT"], row["PRIM_FUEL"], row['PRIM_MVR'])
        u = (row['PLANT'],row['PRIM_FUEL'])
        r = (row['PLANT'],row['NAME'])
        if(row['TYPE'] in sto):
            SOC_max = 1
            SOC_min = 0
            Pchr_max = min(row["WINTER_CAP"],row["SUMMER_CAP"])
            Pdis_max = min(row["WINTER_CAP"],row["SUMMER_CAP"])
            ChargeEfficiency = math.sqrt(sto_dict[row['TYPE']])
            DischargeEfficiency = math.sqrt(sto_dict[row['TYPE']])
            LossFactor = 0.99
            TerminalMax = 0.80
            TerminalMin = 0.20
            SOC_intial = 0.50
            

            csv_writer.writerow([r[0]+'-'+r[1], row['TYPE'],SOC_max, SOC_min, Pchr_max, Pdis_max, ChargeEfficiency, DischargeEfficiency, LossFactor, TerminalMax, TerminalMin, SOC_intial])
            continue
        if tu not in plant_dict:
            if u in Pmin and row["PLANT"] in loc_of_plant:
                if row["ZIP"] in ZipOfsub_dict:
                    min_d = 100000.0
                    for value in ZipOfsub_dict[row["ZIP"]]:
                        # calculate the distance between the plant and substations
                        if (
                            geodesic(loc_of_plant[row["PLANT"]], LocOfsub_dict[value]).m
                            < min_d
                        ):
                            min_d = geodesic(
                                loc_of_plant[row["PLANT"]], LocOfsub_dict[value]
                            ).m
                    bus_id = value
                    pmin = Pmin[u]
                # if this zip does not contain subs, we try to find subs in neighbor zip.
                else:
                    zi = int(row["ZIP"])
                    for i in range(-5, 6):
                        min_d = 100000.0
                        if str(zi + i) in Pmin and str(zi + i) in loc_of_plant:
                            for value in ZipOfsub_dict[str(zi + i)]:
                                if (
                                    geodesic(
                                        loc_of_plant[row["PLANT"]], LocOfsub_dict[value]
                                    ).m
                                    < min_d
                                ):
                                    min_d = geodesic(
                                        loc_of_plant[row["PLANT"]], LocOfsub_dict[value]
                                    ).m
                    bus_id = value
                    pmin = 0
            pmaxwin = row["WINTER_CAP"]
            if pmaxwin < 0.0:
                pmaxwin = 0.0
            pmaxsum = row["SUMMER_CAP"]
            if pmaxsum < 0.0:
                pmaxsum = 0.0
            if(r in points):
                cur = points[r]
 
            else:
                cur = 0
            if r in region:
                re = region[r]
            else:
                if row['STATE'] in West:
                    re = 'Western'
                elif row['STATE'] is 'TX':
                    re = 'Texas'
                else:
                    re = 'Eastern'
            list1 = [bus_id, pmaxwin, pmaxsum, pmin, cur, 1, re, row['TYPE']]
            plant_dict[tu] = list1
        else:
            list1 = plant_dict[tu]
            list1[1] = list1[1] + row["WINTER_CAP"]
            list1[2] = list1[2] + row["SUMMER_CAP"]
            if(r in points):
                list1[4] = list1[4] + points[r]
                list1[5] = list1[5] + 1
            plant_dict[tu] = list1
    storage.close()
    return plant_dict


def write_plant(plant_dict):
    """Write the data to plant.csv as output

    :param dict plant_dict:  a dict of power plants as returned by :func:`Plant_agg`
    """

    
    type_d = {'CONVENTIONAL HYDROELECTRIC' : 'hydro',
              'HYDROELECTRIC PUMPED STORAGE':'hydro', 
              'NATURAL GAS STEAM TURBINE' : 'ng',
              'CONVENTIONAL STEAM COAL' : 'coal',
              'NATURAL GAS FIRED COMBINED CYCLE' : 'ng',
              'NATURAL GAS FIRED COMBUSTION TURBINE': 'ng',
              'PETROLEUM LIQUIDS':'dfo',
              'PETROLEUM COKE':'coal',
              'NATURAL GAS INTERNAL COMBUSTION ENGINE':'ng',
              'NUCLEAR' : 'nuclear',
              'ONSHORE WIND TURBINE':'wind',
              'SOLAR PHOTOVOLTAIC':'solar',
              'GEOTHERMAL':'geothermal',
              'LANDFILL GAS' : 'ng',
              'WOOD/WOOD WASTE BIOMASS' : 'other',
              'COAL INTEGRATED GASIFICATION COMBINED CYCLE' :'coal',
              'OTHER GASES' : 'other',
              'MUNICIPAL SOLID WASTE' : 'other',
              'ALL OTHER':'other',
              'OTHER WASTE BIOMASS' : 'other',
              'OTHER NATURAL GAS' : 'ng',
              'OFFSHORE WIND TURBINE' :'wind_offshore',
              'SOLAR THERMAL WITHOUT ENERGY STORAGE':'solar',
              'SOLAR THERMAL WITH ENERGY STORAGE':'solar'
              }

    with open("output/plant.csv", "w", newline="") as plant:
        csv_writer = csv.writer(plant)
        csv_writer.writerow(
            ["plant_id", "plant_name", "bus_id", "Pg", "status", "Pmax", "Pmin", "ramp_30", "prim_fuel", "interconnect", "type", "GenFuelCost","GenIOB","GenIOC","GenIOD"]
        )
        plant_id = 0
        for key in plant_dict:
            list1 = plant_dict[key]
            csv_writer.writerow(
                [
                    plant_id,
                    key[0] + "-" + key[1],
                    list1[0],
                    list1[3],
                    1,
                    min(list1[1], list1[2]),
                    list1[3],
                    list1[3],
                    key[1],
                    list1[6],
                    type_d[list1[7]],
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                ]
            )
            plant_id = plant_id + 1
    final_bus = set(pd.read_csv("output/bus.csv")["bus_id"])
    final_plant = pd.read_csv("output/plant.csv")
    final_plant = final_plant[final_plant["bus_id"].isin(final_bus)]
    final_plant.to_csv("output/plant.csv", index=False)


def write_gen(plant_dict, type_dict, curve):
    """Write the data to gencost.csv as output

    :param dict plant_dict:  a dict of power plants as returned by :func:`Plant_agg`
    :param dict type_dict:  a dict of generator types
    """
    type_d = {'CONVENTIONAL HYDROELECTRIC' : 'hydro',
              'HYDROELECTRIC PUMPED STORAGE':'hydro', 
              'NATURAL GAS STEAM TURBINE' : 'ng',
              'CONVENTIONAL STEAM COAL' : 'coal',
              'NATURAL GAS FIRED COMBINED CYCLE' : 'ng',
              'NATURAL GAS FIRED COMBUSTION TURBINE': 'ng',
              'PETROLEUM LIQUIDS':'dfo',
              'PETROLEUM COKE':'coal',
              'NATURAL GAS INTERNAL COMBUSTION ENGINE':'ng',
              'NUCLEAR' : 'nuclear',
              'ONSHORE WIND TURBINE':'wind',
              'SOLAR PHOTOVOLTAIC':'solar',
              'GEOTHERMAL':'geothermal',
              'LANDFILL GAS' : 'ng',
              'WOOD/WOOD WASTE BIOMASS' : 'other',
              'COAL INTEGRATED GASIFICATION COMBINED CYCLE' :'coal',
              'OTHER GASES' : 'other',
              'MUNICIPAL SOLID WASTE' : 'other',
              'ALL OTHER':'other',
              'OTHER WASTE BIOMASS' : 'other',
              'OTHER NATURAL GAS' : 'ng',
              'OFFSHORE WIND TURBINE' :'wind_offshore',
              'SOLAR THERMAL WITHOUT ENERGY STORAGE':'solar',
              'SOLAR THERMAL WITH ENERGY STORAGE':'solar'
              }


    with open("output/gencost.csv", "w", newline="") as gencost:
        plant_id = 0
        csv_writer = csv.writer(gencost)
        csv_writer.writerow(["plant_id","plant_name", "type", "n", "c2", "c1", "c0", "interconnect"])
        for key in plant_dict:
            c1 = plant_dict[key][4]/plant_dict[key][5]
            pid = key[0]+'-'+key[1]+'-'+key[2]
            if(pid in curve):
                csv_writer.writerow(
                    [
                        plant_id,
                        key[0] + "-" + key[1] + "-" + key[2],
                        type_d[plant_dict[key][7]],
                        1,
                        curve[pid][0],
                        curve[pid][1],
                        curve[pid][2],
                        plant_dict[key][6]
                    ]
                )
                
            else:
                print(pid)
                csv_writer.writerow(
                    [
                        plant_id,
                        key[0]+ '-'+ key[1] + '-'+key[2],
                        type_d[plant_dict[key][7]],
                        1,
                        '',
                        c1,
                        '',
                        plant_dict[key][6]
                    ]
                    )
            plant_id = plant_id + 1


def Plant(E_csv, U_csv, G2019_csv, Z_csv):
    """Entry point to start the gencost and power plant data processing

    :param str E_csv: path of the HIFLD substation csv file
    :param str U_csv: path of the general unit csv file
    :param str G2019_csv: path of the EIA generator profile csv file
    """

    zone_dic = get_Zone(Z_csv)

    clean_sub = Clean(E_csv, zone_dic)
    LocOfsub_dict, ZipOfsub_dict = LocOfsub(clean_sub)
    loc_of_plant = Loc_of_plant()
    clean_data = Clean_p(U_csv)
    Pmin = Cal_P(G2019_csv)

    type_dict = {}
    type_data = pd.read_csv("data/type.csv")
    for index, row in type_data.iterrows():
        type_dict[row["TYPE"]] = row["Type_code"]
    region = Getregion()
    points = getCostCurve()
    curve = getCostCurve2()
    plant_dict = Plant_agg(clean_data, ZipOfsub_dict, loc_of_plant, LocOfsub_dict, Pmin, region, points)
    write_plant(plant_dict)
    write_gen(plant_dict, type_dict, curve)


if __name__ == "__main__":
    Plant(
        "data/Electric_Substations.csv",
        "data/General_Units.csv",
        "data/Generator_Y2019.csv",
        "data/zone.csv",
    )
