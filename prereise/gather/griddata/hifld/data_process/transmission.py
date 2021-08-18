import os

import pandas as pd
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


def filter_lines_with_unavailable_substations(lines):
    """Filter lines with SUB_1 or SUB_2 attribute equal to 'NOT AVAILABLE', and report
    the number dropped.

    :param pandas.DataFrame lines: data frame of all lines.
    :return: (*pandas.DataFrame*) -- lines with available substations.
    """
    num_lines = len(lines)
    filtered = lines.query("SUB_1 == 'NOT AVAILABLE' or SUB_2 == 'NOT AVAILABLE'")
    num_filtered = len(filtered)
    print(
        f"dropping {num_filtered} lines with one or more substations listed as "
        f"'NOT AVAILABLE' out of a starting total of {num_lines}"
    )
    return lines.query("SUB_1 != 'NOT AVAILABLE' and SUB_2 != 'NOT AVAILABLE'").copy()


def filter_lines_with_no_matching_substations(lines, substations):
    """Filter lines with one or more substation name not present in the ``substations``
    data frame, and report the number dropped.

    :param pandas.DataFrame lines: data frame of lines.
    :param pandas.DataFrame substations: data frame of substations.
    :return: (*pandas.DataFrame*) -- lines with matching substations.
    """
    num_lines = len(lines)
    matching_names = substations["NAME"]  # noqa: F841
    filtered = lines.query(
        "SUB_1 not in @matching_names or SUB_2 not in @matching_names"
    )
    num_filtered = len(filtered)
    print(
        f"dropping {num_filtered} lines with one or more substations not found in "
        f"substations table out of a starting total of {num_lines}"
    )
    return lines.query("SUB_1 in @matching_names and SUB_2 in @matching_names").copy()


def filter_lines_with_nonmatching_substation_coords(lines, substations, threshold=100):
    """Filter lines for which either the starting or ending substation, by name, has
    coordinates judged as too far away (based on the ``threshold`` parameter) from the
    coodinated listed for the line. Additionally, add substation IDs for start and end
    (SUB_1_ID, SUB_2_ID respectively), since substation names aren't unique identifiers.

    :param pandas.DataFrame lines: data frame of lines.
    :param pandas.DataFrame substations: data frame of substations.
    :param int/float threshold: maximum mismatch distance (miles).
    :return: (*pandas.DataFrame*) -- lines with matching substations.
    """

    def find_closest_substation_and_distance(coordinates, name, substations_groupby):
        matching_substations = substations_groupby.get_group(name)
        distances = matching_substations.apply(
            lambda x: haversine(coordinates, (x.LATITUDE, x.LONGITUDE)), axis=1
        )
        return pd.Series([distances.idxmin(), distances.min()], index=["sub", "dist"])

    print("Evaluating endpoint location mismatches... (this may take several minutes)")
    substations_groupby = substations.groupby("NAME")
    # Coordinates are initially (lon, lat); we reverse to (lat, lon) for haversine
    start_subs = lines.apply(
        lambda x: find_closest_substation_and_distance(
            x.loc["COORDINATES"][0][::-1], x.loc["SUB_1"], substations_groupby
        ),
        axis=1,
    )
    end_subs = lines.apply(
        lambda x: find_closest_substation_and_distance(
            x.loc["COORDINATES"][-1][::-1], x.loc["SUB_2"], substations_groupby
        ),
        axis=1,
    )
    # Report the number of lines which will be filtered
    filtered = lines.loc[(start_subs.dist > threshold) | (end_subs.dist > threshold)]
    num_filtered = len(filtered)
    num_lines = len(lines)
    print(
        f"dropping {num_filtered} lines with one or more substations with non-matching "
        f"coordinates out of a starting total of {num_lines}"
    )

    # Add substation IDs to lines dataframe
    lines = lines.assign(SUB_1_ID=start_subs["sub"], SUB_2_ID=end_subs["sub"])
    # Actually perform the filtering
    remaining = lines.loc[(start_subs.dist <= threshold) & (end_subs.dist <= threshold)]
    return remaining.copy()


def filter_lines_with_identical_substation_names(lines):
    """Filter lines with SUB_1 or SUB_2 attributes equal to each other, and report the
    number dropped.

    :param pandas.DataFrame lines: data frame of lines.
    :return: (*pandas.DataFrame*) -- lines with distinct substations.
    """
    num_lines = len(lines)
    filtered = lines.query("SUB_1 == SUB_2")
    num_filtered = len(filtered)
    print(
        f"dropping {num_filtered} lines with matching SUB_1 and SUB_2 out of a "
        f"starting total of {num_lines}"
    )
    return lines.query("SUB_1 != SUB_2").copy()


def build_transmission():
    """Main user-facing entry point."""
    # Load input data
    hifld_substations = get_hifld_electric_substations(const.blob_paths["substations"])
    hifld_substations.set_index("ID", inplace=True)
    hifld_lines = get_hifld_electric_power_transmission_lines(
        const.blob_paths["transmission_lines"]
    )
    hifld_data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    hifld_zones = get_zone(os.path.join(hifld_data_dir, "zone.csv"))  # noqa: F841

    # Filter substations
    substations_with_lines = filter_substations_with_zero_lines(hifld_substations)
    check_for_location_conflicts(substations_with_lines)

    # Filter lines
    lines_with_substations = filter_lines_with_unavailable_substations(hifld_lines)
    lines_with_matching_substations = filter_lines_with_no_matching_substations(
        lines_with_substations, substations_with_lines
    )
    lines_with_matching_substations = filter_lines_with_nonmatching_substation_coords(
        lines_with_matching_substations, substations_with_lines
    )
    lines_with_matching_substations = filter_lines_with_identical_substation_names(
        lines_with_matching_substations
    )
    return lines_with_matching_substations
