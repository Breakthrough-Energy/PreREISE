import csv

import pandas as pd
from geopy.distance import geodesic

from prereise.gather.hiflddata.data_trans import Clean, get_Zone

Max_Value = 3000
Min_Value = 0
coord_precision = ".9f"


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
        Pmin[str(row["Plant Name"]).upper()] = row["Minimum Load (MW)"]
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


def Plant_agg(clean_data, ZipOfsub_dict, loc_of_plant, LocOfsub_dict, Pmin):
    """Aggregate the plant by zip code and build the plant dict with geo-based aggregation

    :return: (*dict*) -- a dict for power plant after aggregation
    """

    plant_dict = {}

    for index, row in clean_data.iterrows():
        tu = (row["PLANT"], row["TYPE"])
        if tu not in plant_dict:
            if row["PLANT"] in Pmin and row["PLANT"] in loc_of_plant:
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
                    pmin = Pmin[row["PLANT"]]
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
            pmaxsum = row["SUMMER_CAP"]
            list1 = [bus_id, pmaxwin, pmaxsum, pmin]
            plant_dict[tu] = list1
        else:
            list1 = plant_dict[tu]
            list1[1] = list1[1] + row["WINTER_CAP"]
            list1[2] = list1[2] + row["SUMMER_CAP"]
            plant_dict[tu] = list1
    return plant_dict


def write_plant(plant_dict):
    """Write the data to plant.csv as output

    :param dict plant_dict:  a dict of power plants as returned by :func:`Plant_agg`
    """

    with open("output/plant.csv", "w", newline="") as plant:
        csv_writer = csv.writer(plant)
        csv_writer.writerow(
            ["plant_id", "bus_id", "Pg", "status", "Pmax", "Pmin", "ramp_30", "type"]
        )
        for key in plant_dict:
            list1 = plant_dict[key]
            csv_writer.writerow(
                [
                    key[0] + "-" + key[1],
                    list1[0],
                    1,
                    "OP",
                    min(list1[1], list1[2]),
                    list1[3],
                    list1[3],
                    key[1],
                ]
            )


def write_gen(plant_dict, type_dict):
    """Write the data to gencost.csv as output

    :param dict plant_dict:  a dict of power plants as returned by :func:`Plant_agg`
    :param dict type_dict:  a dict of generator types
    """

    with open("output/gencost.csv", "w", newline="") as gencost:
        csv_writer = csv.writer(gencost)
        csv_writer.writerow(["plant_id", "type", "n", "c2", "c1", "c0"])
        for key in plant_dict:
            csv_writer.writerow(
                [key[0] + "-" + key[1], key[1], 1, 1, type_dict[key[1]], 0]
            )


def Plant(E_csv, U_csv, G2019_csv):
    """Entry point to start the gencost and power plant data processing

    :param str E_csv: path of the HIFLD substation csv file
    :param str U_csv: path of the general unit csv file
    :param str G2019_csv: path of the EIA generator profile csv file
    """

    zone_dic = get_Zone("data/zone.csv")

    clean_sub = Clean(E_csv, zone_dic)
    LocOfsub_dict, ZipOfsub_dict = LocOfsub(clean_sub)
    loc_of_plant = Loc_of_plant()
    clean_data = Clean_p(U_csv)
    Pmin = Cal_P(G2019_csv)

    type_dict = {}
    type_data = pd.read_csv("data/type.csv")
    for index, row in type_data.iterrows():
        type_dict[row["TYPE"]] = row["Type_code"]
    plant_dict = Plant_agg(clean_data, ZipOfsub_dict, loc_of_plant, LocOfsub_dict, Pmin)
    write_plant(plant_dict)
    write_gen(plant_dict, type_dict)


if __name__ == "__main__":
    Plant(
        "data/Electric_Substations.csv",
        "data/General_Units.csv",
        "data/Generator_Y2019.csv",
    )
