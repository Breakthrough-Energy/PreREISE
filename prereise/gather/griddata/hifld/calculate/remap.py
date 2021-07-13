import copy


def get_zone_mapping(zone):
    """Generate dictionaries of zone using the zone.csv

    :param pandas.DataFrame zone: the zone.csv data
    :return: (*tuple*) -- a tuple of two dictionaries, where the first
    dictionary is a dict mapping the STATE to its ID and the second is a dict
    mapping a tuple of state and interconnect to its ID.
    """

    zone_dic = {}
    zone_interconnect_dic = {}
    for i in range(len(zone)):
        tu = (zone["zone_name"][i], zone["interconnect"][i])
        zone_dic[zone["zone_name"][i]] = zone["zone_id"][i]
        zone_interconnect_dic[tu] = zone["zone_id"][i]
    return zone_dic, zone_interconnect_dic


def get_line_mapping(lines):
    """Create dict to store all the raw transmission line csv data

    :param str t_csv: path of the HIFLD transmission csv file
    :return: (*dict*) -- a dict mapping the transmission ID to its raw parameters.
    """

    raw_data = copy.deepcopy(lines)
    raw_data["ID"] = raw_data["ID"].astype("str")
    raw_lines = raw_data.set_index("ID").to_dict()
    return raw_lines


def get_sub_mapping(clean_data):
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
