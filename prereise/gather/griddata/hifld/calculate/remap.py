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
