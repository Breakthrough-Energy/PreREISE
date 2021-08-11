import os

from powersimdata.utility.distance import haversine

from prereise.gather.griddata.hifld import const
from prereise.gather.griddata.hifld.data_access.load import (
    get_hifld_electric_power_transmission_lines,
    get_hifld_electric_substations,
    get_zone,
)


def check_for_location_conflicts(substations):
    """Check for multiple substations with identical lat/lon.

    :param pandas.DataFrame substations: data frame of substations.
    :raises ValueError: if multiple substations with identical lat/lon.
    """
    num_substations = len(substations)
    num_lat_lon_groups = len(substations.groupby(["LATITUDE", "LONGITUDE"]))
    if num_lat_lon_groups != num_substations:
        num_collisions = num_substations - num_lat_lon_groups
        raise ValueError(
            f"There are {num_collisions} substations with duplicate lat/lon values"
        )

def filter_substations_with_zero_lines(substations):
    """Filter substations with LINES attribute equal to zero, and report the number
    dropped.

    :param pandas.DataFrame substations: data frame of all substations.
    :return: (*pandas.DataFrame*) -- substations with non-zero values for LINES.
    """
    num_substations = len(substations)
    num_substations_without_lines = len(substations.query("LINES == 0"))
    print(
        f"dropping {num_substations_without_lines} substations "
        f"of {num_substations} total due to LINES parameter equal to 0"
    )

    return substations.query("LINES != 0").copy()


def build_transmission():
    """Main user-facing entry point."""
    # Load input data
    hifld_substations = get_hifld_electric_substations(const.blob_paths["substations"])
    hifld_lines = get_hifld_electric_power_transmission_lines(
        const.blob_paths["transmission_lines"]
    )
    hifld_data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    hifld_zones = get_zone(os.path.join(hifld_data_dir, "zone.csv"))  # noqa: F841

    # Filter substations
    substations_with_lines = filter_substations_with_zero_lines(hifld_substations)
    check_for_location_conflicts(substations_with_lines)
