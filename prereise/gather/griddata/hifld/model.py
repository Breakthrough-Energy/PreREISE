from prereise.gather.griddata.hifld.data_access.load import load_csv
from prereise.gather.griddata.hifld.data_access.remap import get_zone_mapping


def get_grid_data(e_csv, t_csv, z_csv):
    """Load HIFLD data and create dataframes corresponding to the input csv's
    for the BES grid.

    :param str e_csv: path of the HIFLD substation csv file
    :param str t_csv: path of the HIFLD transmission csv file
    :param str z_csv: path of the zone csv file
    """

    zone_data = load_csv(z_csv)
    zone_dic, zone_interconnect_dic = get_zone_mapping(zone_data)

    sub_data = load_csv(e_csv, dtypes={"COUNTYFIPS": str})

    line_data = load_csv(t_csv)

    return zone_data, sub_data, line_data
