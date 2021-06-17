import csv
import math

import numpy as np
import pandas as pd
from powersimdata.utility.distance import haversine

coord_precision = ".9f"

West = ["WA", "OR", "CA", "NV", "AK", "ID", "UT", "AZ", "WY", "CO", "NM"]
Uncertain = ["MT", "SD", "TX"]


def get_zone(z_csv):
    """Generate a dictionary of zone using the zone.csv

    :param str z_csv: path of the zone.csv file
    :return: (*dict*) -- a dict mapping the STATE to its ID.
    """
    zone = pd.read_csv(z_csv)

    # Create dictionary to store the mapping of states and codes
    zone_dic = {}
    for i in range(len(zone)):
        zone_dic[zone["zone_name"][i]] = zone["zone_id"][i]
    return zone_dic


def map_plant_county(p_csv):
    """Generate a dictionary of county using the Power_Plants.csv

    :param str p_csv: path of the Power_Plants.csv file
    :return: (*dict*) -- a dict mapping the plant county to its name.
    """
    plant = pd.read_csv(p_csv)
    county_dic = plant.set_index("NAME")["COUNTY"].to_dict()
    return county_dic


def clean(e_csv, zone_dic):
    """Clean data; remove substations which are outside the United States or not available.
    :param str e_csv: path of the HIFLD substation csv file
    :param dict zone_dic: zone dict as returned by :func:`get_zone`
    :return: (*pandas.DataFrame*) -- a pandas Dataframe storing the substations after dropping the invalid ones.
    """
    csv_data = pd.read_csv(e_csv)
    num_sub = len(csv_data)
    row_indexs = []
    for i in range(num_sub):
        if (
            (csv_data["STATE"][i] not in zone_dic)
            or (csv_data["STATUS"][i] != "IN SERVICE")
            or (csv_data["LINES"][i] == 0)
        ):
            row_indexs.append(i)
    clean_data = csv_data.drop(labels=row_indexs)
    return clean_data


def clean_p(p_csv):
    """Clean data; remove plants which are not available.
    :param str p_csv: path of the HIFLD plants csv file
    :param dict zone_dic: zone dict as returned by :func:`get_zone`
    :return: (*pandas.DataFrame*) -- a pandas Dataframe storing the plants after dropping the invalid ones.
    """
    csv_data = pd.read_csv(p_csv)
    num_sub = len(csv_data)
    row_indexs = []
    for i in range(num_sub):
        if csv_data["STATUS"][i] != "OP":
            row_indexs.append(i)
    clean_data = csv_data.drop(labels=row_indexs)
    return clean_data


def map_interconnect_sub(bus_csv):
    """Generate a list of dictionaries of buses in each interconnect using the bus.csv

    :param str bus_csv: Power_Plants of the zone.csv file
    :return: (*dict*) -- a dict mapping the plant county to its name.
    """
    inter_bus = {}
    bus = pd.read_csv(bus_csv)
    inter_bus["Eastern"] = []
    inter_bus["Western"] = []
    inter_bus["Texas"] = []
    for row in bus.iloc:
        inter_bus[row["interconnect"]].append(row["bus_id"])
    return inter_bus


def loc_of_sub(bus_csv):
    """Get the latitude and longitude of substations, and the substations in the area of each zip code

    :param str bus_csv:  path of the sub.csv file
    :return: (*dict*) -- LocOfsub_dict, dict mapping the geo coordinate (x,y) to substations.
    :return: (*dict*) -- ZipOfsub_dict, dict mapping the zip code to a group of substations.
    """
    loc_of_sub_dict = {}
    zip_of_sub_dict = {}
    zip_of_sub_dict["Eastern"] = {}
    zip_of_sub_dict["Western"] = {}
    zip_of_sub_dict["Texas"] = {}
    bus = pd.read_csv(bus_csv)
    for index, row in bus.iterrows():
        loc = (
            format(row["lat"], coord_precision),
            format(row["lon"], coord_precision),
        )

        sub = row["sub_id"]
        zi = str(row["zip"])
        re = row["interconnect"]
        loc_of_sub_dict[sub] = loc

        if zi in zip_of_sub_dict[re]:
            list1 = zip_of_sub_dict[re][zi]
            list1.append(sub)
            zip_of_sub_dict[re][zi] = list1
        else:
            list1 = [sub]
            zip_of_sub_dict[re][zi] = list1
    return loc_of_sub_dict, zip_of_sub_dict


def cal_pmin(g_csv):
    """Calculate the Pmin for each plant

    :param dict g_csv: path of the EIA generator profile csv file
    :return: (*dict*) -- a dict of Pmin for the plants.
    """

    pmin = {}
    csv_data = pd.read_csv(g_csv)
    for index, row in csv_data.iterrows():
        tu = (str(row["Plant Name"]).upper(), row["Energy Source 1"])
        pmin[tu] = row["Minimum Load (MW)"]
    return pmin


def get_loc_of_plant():
    """Get the latitude and longitude of plants

    :return: (*dict*) -- a dict of power plants' geo coordinates.
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


def get_cost_curve():
    """Get the latitude and longitude of plants

    :return: (*dict*) -- a dict of power plants' c1 data.
    """
    points = {}
    csv_data = pd.read_csv("data/needs.csv")
    df = np.array(csv_data)
    cost = df.tolist()
    for pla in cost:
        name = (str(pla[0]).upper(), pla[4])
        points[name] = int(pla[13])
    return points


def get_cost_curve2():
    """Get the latitude and longitude of plants

    :return: (*dict*) -- a dict of power plants' c2,c1,c0 data.
    """
    curve = {}
    csv_data = pd.read_csv("data/curve.csv")
    df = np.array(csv_data)
    cost = df.tolist()
    for pla in cost:
        name = pla[0]
        curve[name] = (pla[1], pla[2], pla[3])
    return curve


def get_region():
    """Get the interconnect of plants
    :return: (*dict*) -- a dict of power plants' interconnect.
    """
    region = {}
    csv_data = pd.read_csv("data/needs.csv")
    df = np.array(csv_data)
    needs = df.tolist()
    for pla in needs:
        name = (str(pla[0]).upper(), pla[4])
        if name not in region:
            if pla[8][0:3] == "ERC":
                re = "Texas"
            elif pla[8][0:3] == "WEC":
                re = "Western"
            else:
                re = "Eastern"
            region[name] = re
    return region


def plant_agg(
    clean_data,
    zip_of_sub_dict,
    loc_of_plant,
    loc_of_sub_dict,
    pmin,
    region,
    points,
    county_dic,
):
    """Aggregate the plant by zip code and build the plant dict with geo-based aggregation

    :return: (*dict*) -- a dict for power plant after aggregation
    """

    plant_dict = {}
    storage = open("output/storage.csv", "w", newline="")
    csv_writer = csv.writer(storage)
    csv_writer.writerow(
        [
            "Storage_name",
            "Type",
            "SOC_max",
            "SOC_min",
            "Pchr_max",
            "Pdis_max",
            "Charge Efficiency",
            "Discharge Efficiency",
            "Loss Factor",
            "Terminal Max",
            "Terminal Min",
            "SOC_intial",
        ]
    )
    sto = ["BATTERIES", "NATURAL GAS WITH COMPRESSED AIR STORAGE", "FLYWHEELS"]
    sto_dict = {
        "BATTERIES": 0.95,
        "NATURAL GAS WITH COMPRESSED AIR STORAGE": 0.50,
        "FLYWHEELS": 0.90,
    }
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
    nm_east = ["CURRY", "LEA", "QUAY", "ROOSEVELT", "UNION"]
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
    for index, row in clean_data.iterrows():
        tu = (row["PLANT"], row["PRIM_FUEL"], row["PRIM_MVR"])
        u = (row["PLANT"], row["PRIM_FUEL"])
        r = (row["PLANT"], row["NAME"])
        if row["TYPE"] in sto:
            soc_max = 1
            soc_min = 0
            pchr_max = min(row["WINTER_CAP"], row["SUMMER_CAP"])
            pdis_max = min(row["WINTER_CAP"], row["SUMMER_CAP"])
            charge_efficiency = math.sqrt(sto_dict[row["TYPE"]])
            discharge_efficiency = math.sqrt(sto_dict[row["TYPE"]])
            loss_factor = 0.99
            terminal_max = 0.80
            terminal_min = 0.20
            soc_intial = 0.50

            csv_writer.writerow(
                [
                    r[0] + "-" + r[1],
                    row["TYPE"],
                    soc_max,
                    soc_min,
                    pchr_max,
                    pdis_max,
                    charge_efficiency,
                    discharge_efficiency,
                    loss_factor,
                    terminal_max,
                    terminal_min,
                    soc_intial,
                ]
            )
            continue

        if r in region:
            re = region[r]
        else:
            if row["PLANT"] in county_dic:
                county = county_dic[row["PLANT"]]
            else:
                # print("no plant",row['PLANT'])
                county = ""
            if row["STATE"] in West:
                re = "Western"
            elif row["STATE"] == "TX":
                if county in tx_west:
                    re = "Western"
                elif county in tx_east:
                    re = "Eastern"
                else:
                    re = "Texas"
            elif row["STATE"] == "SD":
                if county in sd_west:
                    re = "Western"
                else:
                    re = "Eastern"
            elif row["STATE"] == "NM":
                if county in nm_east:
                    re = "Eastern"
                else:

                    re = "Western"
            elif row["STATE"] == "MT":
                if county in mt_east:
                    re = "Eastern"
                else:

                    re = "Western"
            else:
                re = "Eastern"

        if tu not in plant_dict:
            plant_id = row["OBJECTID"]
            bus_id = 100000
            if row["PLANT"] in loc_of_plant:
                lat = loc_of_plant[row["PLANT"]][0]
                lon = loc_of_plant[row["PLANT"]][1]
                # print(u)
                if row["ZIP"] in zip_of_sub_dict[re]:

                    min_d = 1000000.0
                    for value in zip_of_sub_dict[re][row["ZIP"]]:

                        # calculate the distance between the plant and substations
                        if (
                            haversine(
                                loc_of_plant[row["PLANT"]], loc_of_sub_dict[value]
                            )
                            < min_d
                        ):
                            min_d = haversine(
                                loc_of_plant[row["PLANT"]], loc_of_sub_dict[value]
                            )
                            # print(value)

                            bus_id = value

                # if this zip does not contain subs, we try to find subs in neighbor zip.
                else:

                    zi = int(row["ZIP"])

                    min_d = 1000000.0

                    for i in range(-100, 101):
                        if str(zi + i) in zip_of_sub_dict[re]:
                            for value in zip_of_sub_dict[re][str(zi + i)]:
                                # if value not in inter_bus[re]:
                                #    continue
                                # print(value)
                                if row["PLANT"] == "INGLESIDE COGENERATION":
                                    print(
                                        haversine(
                                            loc_of_plant[row["PLANT"]],
                                            loc_of_sub_dict[value],
                                        )
                                    )
                                if (
                                    haversine(
                                        loc_of_plant[row["PLANT"]],
                                        loc_of_sub_dict[value],
                                    )
                                    < min_d
                                ):
                                    min_d = haversine(
                                        loc_of_plant[row["PLANT"]],
                                        loc_of_sub_dict[value],
                                    )
                                    # print(value)

                                    bus_id = value
                    if bus_id == 100000 and re == "Texas":
                        print(row["PLANT"], row["NAME"], row["ZIP"], re)
            else:

                if row["ZIP"] in zip_of_sub_dict[re]:
                    bus_id = zip_of_sub_dict[re][row["ZIP"]][0]
                    lat = loc_of_sub_dict[bus_id][0]
                    lon = loc_of_sub_dict[bus_id][1]
                else:
                    # print(row['PLANT'],row['NAME'],row['ZIP'],re)
                    continue
            if u in pmin:
                pmin = pmin[u]
                pmin = pmin.replace(",", "")
            else:
                pmin = 0.0

            try:
                pmin = float(pmin)
            except ValueError:
                pmin = 0.0
            # else:
            # print(tu)
            pmax = row["NAMPLT_CAP"]
            if pmax < 0.0:
                pmax = 0.0
            if r in points:
                cur = points[r]

            else:
                cur = 0
            # if(bus_id == 100000):
            #    print(row['PLANT'],row['NAME'],row['ZIP'],re)
            list1 = [
                bus_id,
                pmax,
                0,
                pmin,
                cur,
                1,
                re,
                row["TYPE"],
                plant_id,
                min_d,
                lat,
                lon,
                row["ZIP"],
                row["STATE"],
            ]
            plant_dict[tu] = list1
        else:
            list1 = plant_dict[tu]
            if row["NAMPLT_CAP"] > 0:
                list1[1] = list1[1] + row["NAMPLT_CAP"]
            if r in points:
                list1[4] = list1[4] + points[r]
                list1[5] = list1[5] + 1
            plant_dict[tu] = list1
    storage.close()
    return plant_dict


def write_plant(plant_dict):
    """Write the data to plant.csv as output

    :param dict plant_dict:  a dict of power plants as returned by :func:`Plant_agg`
    """

    type_d = {
        "CONVENTIONAL HYDROELECTRIC": "hydro",
        "HYDROELECTRIC PUMPED STORAGE": "hydro",
        "NATURAL GAS STEAM TURBINE": "ng",
        "CONVENTIONAL STEAM COAL": "coal",
        "NATURAL GAS FIRED COMBINED CYCLE": "ng",
        "NATURAL GAS FIRED COMBUSTION TURBINE": "ng",
        "PETROLEUM LIQUIDS": "dfo",
        "PETROLEUM COKE": "coal",
        "NATURAL GAS INTERNAL COMBUSTION ENGINE": "ng",
        "NUCLEAR": "nuclear",
        "ONSHORE WIND TURBINE": "wind",
        "SOLAR PHOTOVOLTAIC": "solar",
        "GEOTHERMAL": "geothermal",
        "LANDFILL GAS": "ng",
        "WOOD/WOOD WASTE BIOMASS": "other",
        "COAL INTEGRATED GASIFICATION COMBINED CYCLE": "coal",
        "OTHER GASES": "other",
        "MUNICIPAL SOLID WASTE": "other",
        "ALL OTHER": "other",
        "OTHER WASTE BIOMASS": "other",
        "OTHER NATURAL GAS": "ng",
        "OFFSHORE WIND TURBINE": "wind_offshore",
        "SOLAR THERMAL WITHOUT ENERGY STORAGE": "solar",
        "SOLAR THERMAL WITH ENERGY STORAGE": "solar",
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
                "distance",
                "lat",
                "lon",
                "zip",
                "state",
            ]
        )
        print(len(plant_dict))
        for key in plant_dict:
            list1 = plant_dict[key]
            pmax = list1[1]
            if pmax < 2 * list1[3]:
                pmax = 2 * list1[3]
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
                    list1[9],
                    list1[10],
                    list1[11],
                    list1[12],
                    list1[13],
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
    :param dict curve:  a dict of consumption curves
    """

    with open("output/gencost.csv", "w", newline="") as gencost:
        csv_writer = csv.writer(gencost)
        csv_writer.writerow(
            [
                "plant_id",
                "type",
                "startup",
                "shutdown",
                "n",
                "c2",
                "c1",
                "c0",
                "interconnect",
            ]
        )
        for key in plant_dict:
            c1 = plant_dict[key][4] / plant_dict[key][5]
            pid = key[0] + "-" + key[1] + "-" + key[2]
            if pid in curve and curve[pid][1] > 0:
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
                        plant_dict[key][6],
                    ]
                )

            else:
                # print(pid)
                csv_writer.writerow(
                    [plant_dict[key][8], 2, 0, 0, 3, 0, c1, 0, plant_dict[key][6]]
                )
    final_gen = pd.read_csv("output/gencost.csv")
    final_plant = set(pd.read_csv("output/plant.csv")["plant_id"])
    final_gen = final_gen[final_gen["plant_id"].isin(final_plant)]
    final_gen.to_csv("output/gencost.csv", index=False)


def plant(u_csv, g2019_csv, p_csv, bus_csv):
    """Entry point to start the gencost and power plant data processing

    :param str e_csv: path of the HIFLD substation csv file
    :param str u_csv: path of the general unit csv file
    :param str g2019_csv: path of the EIA generator profile csv file
    """

    county_dic = map_plant_county(p_csv)
    # inter_bus = map_interconnect_sub(bus_csv)
    loc_of_sub_dict, zip_of_sub_dict = loc_of_sub(bus_csv)
    loc_of_plant = get_loc_of_plant()
    clean_data = clean_p(u_csv)
    pmin = cal_pmin(g2019_csv)

    type_dict = {}
    type_data = pd.read_csv("data/type.csv")
    for index, row in type_data.iterrows():
        type_dict[row["TYPE"]] = row["Type_code"]
    region = get_region()
    points = get_cost_curve()
    curve = get_cost_curve2()
    plant_dict = plant_agg(
        clean_data,
        zip_of_sub_dict,
        loc_of_plant,
        loc_of_sub_dict,
        pmin,
        region,
        points,
        county_dic,
    )
    write_plant(plant_dict)
    write_gen(plant_dict, type_dict, curve)


if __name__ == "__main__":
    plant(
        "data/General_Units.csv",
        "data/Generator_Y2019.csv",
        "data/Power_Plants.csv",
        "output/sub.csv",
    )
