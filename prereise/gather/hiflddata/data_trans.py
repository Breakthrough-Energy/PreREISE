import pandas as pd


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


def clean(e_csv, zone_dic):
    """Clean data; remove substations which are outside the United States or not available.
    :param str e_csv: path of the HIFLD substation csv file
    :param dict zone_dic: zone dict as returned by :func:`get_zone`
    :return: (*pandas.DataFrame*) -- a pandas Dataframe storing the substations after dropping the invalid ones.
    """
    return pd.read_csv(e_csv, dtype={"COUNTYFIPS": str}).query(
        "STATE in @zone_dic and LINES != 0"
    )


def line_from_csv(t_csv):
    """Create dict to store all the raw transmission line csv data

    :param str t_csv: path of the HIFLD transmission csv file
    :return: (*dict*) -- a dict mapping the transmission ID to its raw parameters.
    """

    raw_data = pd.read_csv(t_csv)
    raw_data["ID"] = raw_data["ID"].astype("str")
    raw_lines = raw_data.set_index("ID").to_dict()
    return raw_lines


def data_transform(e_csv, t_csv, z_csv):
    """Entry point to start the HIFLD parsing

    :param str e_csv: path of the HIFLD substation csv file
    :param str t_csv: path of the HIFLD transmission csv file
    :param str z_csv: path of the zone csv file
    """

    zone_dic, zone_dic1 = get_zone(z_csv)

    clean_data = clean(e_csv, zone_dic)
    raw_lines = line_from_csv(t_csv)
    print(len(clean_data))
    print(len(raw_lines))


if __name__ == "__main__":
    data_transform(
        "data/Electric_Substations.csv",
        "data/Electric_Power_Transmission_Lines.csv",
        "data/zone.csv",
    )
