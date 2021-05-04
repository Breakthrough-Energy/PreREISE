import csv
import math
import numpy as np
import pandas as pd
from geopy.distance import geodesic

from data_trans import clean, get_Zone

coord_precision = ".9f"

West = ['WA','OR','CA','NV','AK','ID','UT','AZ','WY','CO','NM']
Uncertain = ['MT','SD','TX']


def get_Zone(Z_csv):
    zone = pd.read_csv(Z_csv)

    # Create dictionary to store the mapping of states and codes
    zone_dic = {}
    for i in range(len(zone)):
        zone_dic[zone["zone_name"][i]] = zone["zone_id"][i]
    return zone_dic

def map_plant_county(P_csv):
    plant = pd.read_csv(P_csv)
    county_dic = plant.set_index('NAME')['COUNTY'].to_dict()
    return county_dic

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

def map_interconnect_sub(bus_csv):
    inter_bus = {}
    bus = pd.read_csv(bus_csv)
    inter_bus['Eastern'] = []
    inter_bus['Western'] = []
    inter_bus['Texas'] = []
    for row in bus.iloc:
        inter_bus[row['interconnect']].append(row['bus_id'])
    return inter_bus


def LocOfsub(bus_csv):
    """Get the latitude and longitude of substations, and the substations in the area of each zip code

    :param dict clean_data:  a dict of substations as returned by :func:`data_trans.Clean`
    :return: (*dict*) -- LocOfsub_dict, dict mapping the geo coordinate (x,y) to substations.
    :return: (*dict*) -- ZipOfsub_dict, dict mapping the zip code to a group of substations.
    """
    LocOfsub_dict = {}
    ZipOfsub_dict = {}
    ZipOfsub_dict['Eastern'] = {}
    ZipOfsub_dict['Western'] = {}
    ZipOfsub_dict['Texas'] = {}
    bus = pd.read_csv(bus_csv)
    for index, row in bus.iterrows():
        loc = (
            format(row["lat"], coord_precision),
            format(row["lon"], coord_precision),
        )

        sub = row["sub_id"]
        zi = str(row["zip"])
        re = row["interconnect"]
        LocOfsub_dict[sub] = loc

        if zi in ZipOfsub_dict[re]:
            list1 = ZipOfsub_dict[re][zi]
            list1.append(sub)
            ZipOfsub_dict[re][zi] = list1
        else:
            list1 = [sub]
            ZipOfsub_dict[re][zi] = list1
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

def Plant_agg(clean_data, ZipOfsub_dict, loc_of_plant, LocOfsub_dict, Pmin, region, points, county_dic):
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
    tx_west = ['EL PASO','HUDSPETH']
    tx_east = ['BOWIE','MORRIS','CASS','CAMP','UPSHUR','GREGG','MARION','HARRISON','PANOLA','SHELBY','SAN AUGUSTINE','SABINE','JASPER','NEWTON',
               'ORANGE','JEFFERSON','LIBERTY','HARDIN','TYLER','POLK','TRINITY','WALKER','SAN JACINTO','DALLAM','SHERMAN','HANSFORD','OCHLTREE'
               'LIPSCOMB','HARTLEY','MOORE','HUTCHINSON','HEMPHILL','RANDALL','DONLEY','PARMER','BAILEY','LAMB','HALE','COCHRAN','HOCKLEY','LUBBOCK',
               'YOAKUM','TERRY','LYNN','GAINES']
    sd_west = ['LAWRENCE', 'BUTTE', 'FALL RIVER']
    nm_east = ['CURRY', 'LEA', 'QUAY', 'ROOSEVELT', 'UNION']
    mt_east = ['CARTER','CUSTER','ROSEBUD','PRAIRIE','POWDER RIVER','DANIELS','MCCONE','DAWSON','RICHLAND','FALLON',
               'GARFIELD','ROOSEVELT','PHILLIPS','SHERIDAN','VALLEY','WIBAUX']            
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
        
        if r in region:
                re = region[r]
        else:
            if(row['PLANT'] in county_dic):
                county = county_dic[row['PLANT']]
            else:
                #print("no plant",row['PLANT'])
                county = ''
            if row['STATE'] in West:
                re = 'Western'
            elif row['STATE'] is 'TX':
                if county in tx_west:
                    re = 'Western'
                elif county in tx_east:
                    re = 'Eastern'
                else:
                    re = 'Texas'
            elif row['STATE'] == 'SD':
                if county in sd_west:
                    re = 'Western'
                else:
                    re = 'Eastern'
            elif row['STATE'] == 'NM':
                if county in nm_east:
                    re = 'Eastern'
                else:
                    #code = zone_dic1[(row['STATE'],re)]
                    re = 'Western'
            elif row['STATE'] == 'MT':
                if county in mt_east:
                    re = 'Eastern'
                else:
                    #code = zone_dic1[(row['STATE'],re)]
                    re = 'Western'
            else:
                    re = 'Eastern'
        
        if tu not in plant_dict:
            plant_id = row['OBJECTID']
            bus_id = 100000
            if row["PLANT"] in loc_of_plant:
                #print(u)
                if row["ZIP"] in ZipOfsub_dict[re]:
                    #if(re == 'Texas'):
                        #print(row["ZIP"])

                    #print(u)
                    min_d = 1000000.0
                    for value in ZipOfsub_dict[re][row["ZIP"]]:

                        # calculate the distance between the plant and substations
                        if (
                            geodesic(loc_of_plant[row["PLANT"]], LocOfsub_dict[value]).m
                            < min_d
                        ):
                            min_d = geodesic(
                                loc_of_plant[row["PLANT"]], LocOfsub_dict[value]
                            ).m
                            #print(value)

                            bus_id = value
                    #if(bus_id == 100000 and re =='Texas'):
                    #    print(row['PLANT'],row['NAME'],row['ZIP'],re)

                # if this zip does not contain subs, we try to find subs in neighbor zip.
                else:
                    
                    zi = int(row["ZIP"])
                    
                    min_d = 1000000.0
                    
 
                    for i in range(-100, 101):                        
                        if str(zi + i) in ZipOfsub_dict[re]:
                            for value in ZipOfsub_dict[re][str(zi + i)]:
                                #if value not in inter_bus[re]:
                                #    continue
                                #print(value)
                                if(row["PLANT"] == 'INGLESIDE COGENERATION'):
                                    print(geodesic(
                                        loc_of_plant[row["PLANT"]], LocOfsub_dict[value]
                                    ).m)
                                if (
                                    geodesic(
                                        loc_of_plant[row["PLANT"]], LocOfsub_dict[value]
                                    ).m
                                    < min_d
                                ):
                                    min_d = geodesic(
                                        loc_of_plant[row["PLANT"]], LocOfsub_dict[value]
                                    ).m
                                    #print(value)

                                    bus_id = value
                    if(bus_id == 100000 and re =='Texas'):
                        print(row['PLANT'],row['NAME'],row['ZIP'],re)
            else:
                if row["ZIP"] in ZipOfsub_dict[re]:
                    bus_id = ZipOfsub_dict[re][row["ZIP"]][0]
                else:
                    #print(row['PLANT'],row['NAME'],row['ZIP'],re)
                    continue
            if(u in Pmin): 
                pmin = Pmin[u]
                pmin = pmin.replace(',','')
            else:
                pmin = 0.0

            try:
                pmin = float(pmin)
            except:
                pmin = 0.0
            #else:
                #print(tu)
            pmax = row["NAMPLT_CAP"]
            if pmax < 0.0:
                pmax = 0.0
            if(r in points):
                cur = points[r]
 
            else:
                cur = 0
            #if(bus_id == 100000):
            #    print(row['PLANT'],row['NAME'],row['ZIP'],re)
            list1 = [bus_id, pmax, 0, pmin, cur, 1, re, row['TYPE'], plant_id,min_d]
            plant_dict[tu] = list1
        else:
            list1 = plant_dict[tu]
            if row["NAMPLT_CAP"] > 0:
                list1[1] = list1[1] + row["NAMPLT_CAP"]
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
            [
                "plant_id",
                "bus_id",
                "Pg",
                "Qg",
                "Qmax",
                "Qmin",
                "Vg",
                "mBase",
                "status",
                "Pmax",
                "Pmin",
                "Pc1",
                "Pc2",
                "Qc1min",
                "Qc1max",
                "Qc2min",
                "Qc2max",
                "ramp_agc",
                "ramp_10",
                "ramp_30",
                "ramp_q",
                "apf",
                "mu_Pmax",
                "mu_Pmin",
                "mu_Qmax",
                "mu_Qmin",
                "type",
                "interconnect",
                "GenFuelCost",
                "GenIOB",
                "GenIOC",
                "GenIOD",
                "distance"]
        )
        print(len(plant_dict))
        for key in plant_dict:
            list1 = plant_dict[key]
            pmax = list1[1]
            if(pmax < 2*list1[3]):
                pmax = 2*list1[3]
            csv_writer.writerow(
                [
                    list1[8],
                    list1[0],
                    list1[3],
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    1,
                    pmax,
                    list1[3],
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    list1[3],
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    type_d[list1[7]],
                    list1[6],
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    list1[9]
                ]
            )
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
        csv_writer = csv.writer(gencost)
        csv_writer.writerow(["plant_id","type", "startup","shutdown","n", "c2", "c1", "c0", "interconnect"])
        for key in plant_dict:
            c1 = plant_dict[key][4]/plant_dict[key][5]
            pid = key[0]+'-'+key[1]+'-'+key[2]
            if(pid in curve and curve[pid][1] > 0):
                csv_writer.writerow(
                    [
                        plant_dict[key][8],
                        2,
                        0,
                        0,
                        3,
                        curve[pid][0],
                        curve[pid][1],
                        curve[pid][2],
                        plant_dict[key][6]
                    ]
                )
                
            else:
                #print(pid)
                csv_writer.writerow(
                    [
                        plant_dict[key][8],
                        2,
                        0,
                        0,
                        3,
                        0,
                        c1,
                        0,
                        plant_dict[key][6]
                    ]
                    )
    final_gen = pd.read_csv("output/gencost.csv")
    final_plant = set(pd.read_csv("output/plant.csv")["plant_id"])
    final_gen = final_gen[final_gen["plant_id"].isin(final_plant)]
    final_gen.to_csv("output/gencost.csv", index=False)


def Plant(E_csv, U_csv, G2019_csv, Z_csv, P_csv, bus_csv):
    """Entry point to start the gencost and power plant data processing

    :param str E_csv: path of the HIFLD substation csv file
    :param str U_csv: path of the general unit csv file
    :param str G2019_csv: path of the EIA generator profile csv file
    """

    zone_dic = get_Zone(Z_csv)
    county_dic = map_plant_county(P_csv)
    #inter_bus = map_interconnect_sub(bus_csv)
    clean_sub = Clean(E_csv, zone_dic)
    LocOfsub_dict, ZipOfsub_dict = LocOfsub(bus_csv)
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
    plant_dict = Plant_agg(clean_data, ZipOfsub_dict, loc_of_plant, LocOfsub_dict, Pmin, region, points,county_dic)
    write_plant(plant_dict)
    write_gen(plant_dict, type_dict, curve)


if __name__ == "__main__":
    Plant(
        "data/Electric_Substations.csv",
        "data/General_Units.csv",
        "data/Generator_Y2019.csv",
        "data/zone.csv",
        "data/Power_Plants.csv",
        "output/sub.csv",
    )
