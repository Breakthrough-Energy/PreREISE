import csv

import pandas as pd
from haversine import Unit, haversine

from prereise.gather.hiflddata.data_trans import clean, get_zone


def clean_p(p_csv):
    csv_data = pd.read_csv(p_csv)
    num_sub = len(csv_data)
    row_indexes = []
    for i in range(num_sub):
        if csv_data["STATUS"][i] != "OP":
            row_indexes.append(i)
    clean_data = csv_data.drop(labels=row_indexes)
    return clean_data


def loc_of_sub(clean_data):
    """Get the latitude and longitude of substations, and the substations in the area of each zip code

    :param dict clean_data:  a dict of substations as returned by :func:`data_trans.clean`
    :return: (*dict*) -- loc_of_sub_dict, dict mapping the geo coordinate (x,y) to substations.
    :return: (*dict*) -- zip_of_sub_dict, dict mapping the zip code to a group of substations.
    """

    loc_of_sub_dict = {}
    zip_of_sub_dict = {}
    for index, row in clean_data.iterrows():
        loc = (
            round(row["LATITUDE"], 9),
            round(row["LONGITUDE"], 9),
        )
        sub = row["ID"]
        zi = row["ZIP"]
        loc_of_sub_dict[sub] = loc
        if zi in zip_of_sub_dict:
            list1 = zip_of_sub_dict[zi]
            list1.append(sub)
            zip_of_sub_dict[zi] = list1
        else:
            list1 = [sub]
            zip_of_sub_dict[zi] = list1
    return loc_of_sub_dict, zip_of_sub_dict


def cal_p(g_csv):
    """Calculate the p_min for each plant

    :param dict g_csv: path of the EIA generator profile csv file
    :return: (*dict*) -- a dict of plant name to minimum load.
    """

    p_min = {}
    csv_data = pd.read_csv(g_csv)
    for index, row in csv_data.iterrows():
        p_min[str(row["Plant Name"]).upper()] = row["Minimum Load (MW)"]
    return p_min


def location_of_plant():
    """Get the latitude and longitude of plants

    :return: (*dict*) -- a dict of power plant name to power plants' geo coordinates.
    """

    loc_of_plant = {}
    csv_data = pd.read_csv("data/Power_Plants.csv")
    for index, row in csv_data.iterrows():
        loc = (
            round(row["LATITUDE"], 9),
            round(row["LONGITUDE"], 9),
        )
        loc_of_plant[row["NAME"]] = loc
    return loc_of_plant


def plant_agg(clean_data, zip_of_sub_dict, loc_of_plant, loc_of_sub_dict, p_min):
    """Aggregate the plant by zip code and build the plant dict with geo-based aggregation

    :param dict clean_data:  a dict of substations as returned by :func:`data_trans.clean`
    :param dict zip_of_sub_dict:  a dict mapping the zip code to a group of substations.
    :param dict loc_of_plant:  a dict of power plant name to power plants' geo coordinates.
    :param dict p_min:  a dict of plant name to minimum load.
    :return: (*dict*) -- a dict for power plant after aggregation
    """

    plant_dict = {}

    for index, row in clean_data.iterrows():
        tu = (row["PLANT"], row["TYPE"])
        if tu not in plant_dict:
            if row["PLANT"] in p_min and row["PLANT"] in loc_of_plant:
                if row["ZIP"] in zip_of_sub_dict:
                    min_d = 100000.0
                    for value in zip_of_sub_dict[row["ZIP"]]:
                        # calculate the distance between the plant and substations
                        min_d = min(
                            haversine(
                                loc_of_plant[row["PLANT"]],
                                loc_of_sub_dict[value],
                                Unit.METERS,
                            ),
                            min_d,
                        )
                    bus_id = value
                    pmin = p_min[row["PLANT"]]
                # if this zip does not contain subs, we try to find subs in neighbor zip.
                else:
                    zi = int(row["ZIP"])
                    for i in range(-5, 6):
                        min_d = 100000.0
                        if str(zi + i) in p_min and str(zi + i) in loc_of_plant:
                            for value in zip_of_sub_dict[str(zi + i)]:
                                min_d = min(
                                    haversine(
                                        loc_of_plant[row["PLANT"]],
                                        loc_of_sub_dict[value],
                                        Unit.METERS,
                                    ),
                                    min_d,
                                )
                    bus_id = value
                    pmin = 0
            p_max_win = row["WINTER_CAP"]
            p_max_sum = row["SUMMER_CAP"]
            list1 = [bus_id, p_max_win, p_max_sum, pmin]
            plant_dict[tu] = list1
        else:
            list1 = plant_dict[tu]
            list1[1] = list1[1] + row["WINTER_CAP"]
            list1[2] = list1[2] + row["SUMMER_CAP"]
            plant_dict[tu] = list1
    return plant_dict


def write_plant(plant_dict):
    """Write the data to plant.csv as output

    :param dict plant_dict:  a dict of power plants as returned by :func:`plant_agg`
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

    :param dict plant_dict:  a dict of power plants as returned by :func:`plant_agg`
    :param dict type_dict:  a dict of generator types
    """

    with open("output/gencost.csv", "w", newline="") as gencost:
        csv_writer = csv.writer(gencost)
        csv_writer.writerow(["plant_id", "type", "n", "c2", "c1", "c0"])
        for key in plant_dict:
            csv_writer.writerow(
                [key[0] + "-" + key[1], key[1], 1, 1, type_dict[key[1]], 0]
            )


def plant(e_csv, u_csv, g_2019_csv, z_csv):
    """Entry point to start the gencost and power plant data processing

    :param str e_csv: path of the HIFLD substation csv file
    :param str u_csv: path of the general unit csv file
    :param str g_2019_csv: path of the EIA generator profile csv file
    """

    zone_dic = get_zone(z_csv)

    clean_sub = clean(e_csv, zone_dic)
    loc_of_sub_dict, zip_of_sub_dict = loc_of_sub(clean_sub)
    loc_of_plant = location_of_plant()
    clean_data = clean_p(u_csv)
    p_min = cal_p(g_2019_csv)

    type_dict = {}
    type_data = pd.read_csv("data/type.csv")
    for index, row in type_data.iterrows():
        type_dict[row["TYPE"]] = row["Type_code"]
    plant_dict = plant_agg(
        clean_data, zip_of_sub_dict, loc_of_plant, loc_of_sub_dict, p_min
    )
    write_plant(plant_dict)
    write_gen(plant_dict, type_dict)


if __name__ == "__main__":
    plant(
        "data/Electric_Substations.csv",
        "data/General_Units.csv",
        "data/Generator_Y2019.csv",
        "data/zone.csv",
    )
