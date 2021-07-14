import copy

import pandas as pd


def get_zone_mapping(zone):
    """Generate dictionaries of zone using the zone.csv

    :param pandas.DataFrame zone: the zone.csv data
    :return: (*tuple*) -- a tuple of two dictionaries, where the first
        dictionary is a dict mapping the zone_name to its zone_id and the
        second is a dict mapping a tuple of state and interconnect to its
        zone_name.
    """

    zone = pd.Series(zone.zone_id, index=zone.zone_name).to_dict()
    zone_interconnect = pd.Series(
        zone.zone_id, index=zip(zone.zone_name, zone.interconnect)
    ).to_dict()

    return zone, zone_interconnect


def get_line_mapping(lines):
    """Create dict to store all the raw transmission line csv data

    :param str lines: path of the HIFLD transmission csv file
    :return: (*dict*) -- a dict mapping the transmission ID to its raw parameters.
    """

    raw_data = copy.deepcopy(lines)
    raw_data["ID"] = raw_data["ID"].astype("str")
    raw_lines = raw_data.set_index("ID").to_dict()
    return raw_lines


def get_sub_mapping(clean_data):
    """Generate the subs

    :param str clean_data: cleaned HIFLD substation csv data
    :return: (*tuple*) --  a tuple of two dictionaries, where the first
        dictionary is sub_by_coord, a dict mapping from (x, y) to substation
        detail, and the second is sub_name, a dict mapping from substation name
        to its coordinate (x, y).
    """

    sub_by_coord = {}
    sub_name = {"sub": []}
    for index, row in clean_data.iterrows():
        location = (row["LATITUDE"], row["LONGITUDE"])
        if location in sub_by_coord:
            raise Exception(
                f"WARNING: substations coordinates conflict check: {location}"
            )
        sub_by_coord[location] = (
            row["ID"],
            row["NAME"],
            row["STATE"],
            row["COUNTY"],
        )
        if row["NAME"] not in sub_name:
            sub_name[row["NAME"]] = []
        sub_name[row["NAME"]].append((row["LATITUDE"], row["LONGITUDE"]))
    return sub_by_coord, sub_name
