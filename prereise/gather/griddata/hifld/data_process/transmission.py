import os

import networkx as nx
import numpy as np
import pandas as pd
from powersimdata.utility.distance import haversine, ll2uv
from scipy.spatial import KDTree
from tqdm import tqdm

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


def map_lines_to_substations_using_coords(substations, lines, **kwargs):
    """Map lines to substations using coordinates.

    :param pandas.DataFrame substations: data frame of substations.
    :param pandas.DataFrame lines: data frame of all lines.
    :param \\*\\*kwargs: optional arguments.
    :return: (*tuple*) -- lines and substations data frame.
    """
    # Optional parameters
    rounding = 3 if "rounding" not in kwargs else kwargs["rounding"]
    drop_zero_distance_line = (
        True
        if "drop_zero_distance_line" not in kwargs
        else kwargs["drop_zero_distance_line"]
    )

    # Round coordinates of substations and lines' endpoints
    print(
        "assigning substations to lines' endpoints by mapping their rounded "
        f"({rounding} digits) coordinates"
    )
    subcoord2subid = (
        substations.round(rounding).groupby(["LATITUDE", "LONGITUDE"]).groups
    )
    lines_coord = lines["COORDINATES"].map(
        lambda x: list(np.round([x[0], x[-1]], rounding))
    )
    line2sub = pd.DataFrame(
        lines_coord.to_list(), columns=["FROM", "TO"], index=lines_coord.index
    ).applymap(tuple)

    # Map coordinates of lines' endpoints to coordinates of substations and add id of
    # matched substations to data frame. Values can be single id, a list of id or NaN
    # (no match)
    end_sub = {"FROM": "SUB_1", "TO": "SUB_2"}
    for e, e_sub in end_sub.items():
        line2sub[e_sub] = line2sub[e].apply(
            lambda x: list(subcoord2subid[x]) if x in subcoord2subid else np.NaN
        )

    # Remove zero-distance lines
    if drop_zero_distance_line:
        idx = line2sub["FROM"].compare(line2sub["TO"]).index
        print(
            f"dropping {lines.shape[0] - len(idx)} lines having same endpoints "
            "coordinates after rounding"
        )
        line2sub = line2sub.loc[idx]

    # Find closest neighbor(s) of unmapped lines' endpoints
    print("finding closest substation to unmapped lines' endpoint(s)")
    subcoord = list(subcoord2subid)
    missing_points = set().union(
        *[
            set(line2sub.loc[line2sub[e_sub].isna(), e].apply(lambda x: (x[1], x[0])))
            for e, e_sub in end_sub.items()
        ]
    )
    tree = KDTree([ll2uv(p[0], p[1]) for p in subcoord])
    endpoint2neighbor = {
        (p[1], p[0]): subcoord2subid[subcoord[tree.query(ll2uv(p[0], p[1]))[1]]]
        for p in tqdm(missing_points, total=len(missing_points))
    }
    filled_subs = [
        line2sub.loc[line2sub[e_sub].isna(), e].map(endpoint2neighbor).map(list)
        for e, e_sub in end_sub.items()
    ]
    line2sub.update(pd.concat(filled_subs, axis=1).rename(columns=end_sub))

    # pick unique substation at each end. Order of preference:
    # SUBSTATION --> TAP --> RISER --> DEAD END
    all2one = {
        tuple(i): None for j in end_sub.values() for i in line2sub[j] if len(i) > 1
    }
    for a in all2one:
        type2id = substations.loc[list(a)].reset_index().groupby("TYPE").first()["ID"]
        for t in ["SUBSTATION", "TAP", "RISER", "DEAD END"]:
            try:
                all2one[a] = type2id.loc[t]
                break
            except KeyError:
                continue
    one2all = {v: k for k, v in all2one.items()}

    # Build substations data frame
    new_substations = substations.copy()
    new_substations = substations.loc[
        set(pd.concat([line2sub[e] for e in end_sub.values()]).explode())
    ]
    new_substations["OTHER_SUB"] = (
        new_substations.reset_index()["ID"]
        .apply(lambda x: list(set(one2all[x]) - {x}) if x in one2all else None)
        .values
    )

    # Build lines data frame
    new_lines = lines.copy()
    new_lines = new_lines.loc[line2sub.index]
    for e_sub in end_sub.values():
        primary_sub = line2sub[e_sub].apply(
            lambda x: all2one[tuple(x)] if len(x) > 1 else x[0]
        )
        new_lines[e_sub] = substations.loc[primary_sub.values, "NAME"].values
        new_lines[f"{e_sub}_ID"] = primary_sub.values

    return new_lines, new_substations


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
            x.loc["COORDINATES"][0], x.loc["SUB_1"], substations_groupby
        ),
        axis=1,
    )
    end_subs = lines.apply(
        lambda x: find_closest_substation_and_distance(
            x.loc["COORDINATES"][-1], x.loc["SUB_2"], substations_groupby
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


def filter_by_connected_components(lines, substations):
    """Filter substations that are not present in the largest connected component that
    is created from interpreting the``lines`` data frame, and report how many are
    filtered this way.

    :param pandas.DataFrame lines: data frame of lines.
    :param pandas.DataFrame substations: data frame of substations.
    :return: (*tuple*) -- two pandas.DataFrames:
        lines connected to largest connected component.
        substations connected to largest connected component.
    """
    graph = nx.convert_matrix.from_pandas_edgelist(lines, "SUB_1_ID", "SUB_2_ID")
    largest_component_subs = set(max(nx.connected_components(graph), key=len))

    filtered_subs = set(substations.index) - largest_component_subs
    filtered_lines = lines.query("SUB_1_ID not in @largest_component_subs")
    print(
        f"dropping {len(filtered_subs)} substations not connected to largest island "
        f"out of a starting total of {len(substations)}"
    )
    print(
        f"dropping {len(filtered_lines)} lines not connected to largest island "
        f"out of a starting total of {len(lines)}"
    )

    remaining_substations = substations.query("index in @largest_component_subs").copy()
    remaining_lines = lines.query("SUB_1_ID in @largest_component_subs").copy()
    return remaining_lines, remaining_substations


def augment_line_voltages(
    lines, substations, volt_class_defaults=None, state_threshold_100_161=0.95
):
    """Fill in voltages for lines with missing voltages, using a series of heuristics.
    The ``lines`` dataframe will be modified in-place.

    :param pandas.DataFrame lines: data frame of lines.
    :param pandas.DataFrame substations: data frame of substations.
    :param dict/pandas.Series volt_class_defaults: mapping of volt classes to default
        replacement voltage values. If None, internally-defined defaults will be used.
    :param int/float state_threshold_100_161: fraction of lines in the 100-161 kV range
        which must be the same voltage for the most common voltage to be applied to
        missing voltage lines in this state.
    """

    def map_via_neighbor_voltages(lines, neighbors, func, method_name):
        """For each line with a missing voltage, iterative find non-missing voltages of
        neighboring lines, apply a function to these lines to determine updates, halting
        once no more updates can be found.

        :param pandas.DataFrame lines: data frame of lines.
        :param pandas.Series neighbors: mapping of line indices to set of neighboring
            line indices.
        :param function func: function to apply to sets of neighboring voltages.
        :param str method_name: method name to print once no more updates can be found.
        """
        while True:
            missing = lines.query("VOLTAGE.isnull()")
            if len(missing) == 0:
                break
            found_voltages = missing.apply(
                lambda x: {
                    v
                    for v in set(lines.loc[neighbors.loc[x.name], "VOLTAGE"])
                    if v == v  # this eliminates float("nan") values from the set
                },
                axis=1,
            )
            assigned_voltages = found_voltages.apply(func)
            if assigned_voltages.isna().all():
                print(
                    f"{len(missing)} line voltages can't be found via neighbor "
                    + method_name
                )
                break
            lines.loc[
                lines.VOLTAGE.isna() & ~assigned_voltages.isna(), "VOLTAGE"
            ] = assigned_voltages.loc[~assigned_voltages.isna()]

    # Interpret input parameters
    if volt_class_defaults is None:
        volt_class_defaults = const.volt_class_defaults

    # Set voltages based on voltage class defaults
    null_voltages = lines.loc[lines.VOLTAGE.isna()]
    replacement_voltages = null_voltages.VOLT_CLASS.map(volt_class_defaults)
    lines.loc[lines.VOLTAGE.isna(), "VOLTAGE"] = replacement_voltages

    # Use commonly-assigned voltages by state to fill 100-161 kV range
    # Assume state grouping on one end is representative
    missing_mask = lines.VOLTAGE.isna()
    class_100_161_mask = lines.VOLT_CLASS == "100-161"
    lines["STATE_1"] = lines.SUB_1_ID.map(substations.STATE)
    lines["STATE_2"] = lines.SUB_2_ID.map(substations.STATE)
    lines["sorted_states"] = lines[["STATE_1", "STATE_2"]].apply(
        lambda x: tuple(sorted(x)), axis=1
    )
    states_100_161_lines = {
        states: group.query("100 <= VOLTAGE <= 161").value_counts(
            "VOLTAGE", normalize=True
        )
        for states, group in lines.groupby("sorted_states")
    }
    most_common_100_161_voltage = {
        states: voltages.idxmax() if voltages.max() > state_threshold_100_161 else None
        for states, voltages in states_100_161_lines.items()
    }
    lines.loc[missing_mask & class_100_161_mask, "VOLTAGE"] = lines.loc[
        missing_mask & class_100_161_mask
    ].sorted_states.map(most_common_100_161_voltage)
    lines.drop(["STATE_1", "STATE_2", "sorted_states"], axis=1, inplace=True)

    # Create a mapping of lines to neighboring lines
    sub_1_lines = pd.Series(lines.groupby("SUB_1_ID").groups).apply(set)
    sub_2_lines = pd.Series(lines.groupby("SUB_2_ID").groups).apply(set)
    sub_lines = sub_1_lines.combine(sub_2_lines, set.union, fill_value=set())
    neighbors = lines.loc[lines.VOLTAGE.isna()].apply(
        lambda x: sub_lines.loc[x.SUB_1_ID] | sub_lines.loc[x.SUB_2_ID], axis=1
    )

    # Update lines with missing voltage if only one voltage exists among their neighbors
    map_via_neighbor_voltages(
        lines, neighbors, lambda x: list(x)[0] if len(x) == 1 else None, "consensus"
    )

    # Update lines with missing voltage using lowest voltage among their neighbors
    map_via_neighbor_voltages(
        lines, neighbors, lambda x: min(x) if len(x) > 0 else None, "minimum"
    )

    # Ensure that voltages are floats
    lines["VOLTAGE"] = lines["VOLTAGE"].astype(float)


def create_buses(lines):
    """Using line and substation information, create a bus within each substation and a
    mapping of buses to substations.

    :param pandas.DataFrame lines: data frame of lines.
    :return: (*pandas.DataFrame*) -- columns are 'baseKV' and 'sub_id'
    """
    sub1_volt = lines.groupby("SUB_1_ID")["VOLTAGE"].apply(set)
    sub2_volt = lines.groupby("SUB_2_ID")["VOLTAGE"].apply(set)
    sub_volt = sub1_volt.combine(sub2_volt, set.union, fill_value=set()).apply(sorted)
    # Get the set of voltages for any line(s) connected to each substation
    buses = sub_volt.explode()
    buses = buses.loc[~buses.isna()]
    buses = buses.astype(float)
    buses.index.name = "sub_id"
    buses = buses.to_frame(name="baseKV").reset_index()

    return buses


def create_transformers(bus):
    """Add transformers between buses within the same substation. The assumed topology
    is that the highest-voltage bus in each substation is connected via a tansformer to
    every other voltage.

    :param pandas.DataFrame bus: columns 'sub_id' and 'baseKV'
    :return: (*pandas.DataFrame*) -- each row is one transformer, columns are
        ["from_bus_id", "to_bus_id"].
    """
    bus_pairs = [
        (b, volt_series.idxmax())
        for sub, volt_series in bus.groupby("sub_id")["baseKV"]
        for b in volt_series.sort_values().index[:-1]
        if len(volt_series) > 1
    ]

    return pd.DataFrame(bus_pairs, columns=["from_bus_id", "to_bus_id"])


def build_transmission(method="sub2line", kwargs={"rounding": 3}):
    """Build transmission network

    :param str method: method used to build network. Default method is *sub2line*
        where all substations are considered and lines are filtered accordingly. Other
        method is *line2sub* where all lines are considered and a list of substations
        is compiled.
    :param dict kwargs: keyword arguments to be passed to functions.
    :raises TypeError:
        if ``method`` is not a str.
        if ``kwargs`` is not a dict.
    :raises ValueError: if ``method`` is unknown.
    """
    if not isinstance(method, str):
        raise TypeError("method must be a str")
    if not isinstance(kwargs, dict):
        raise TypeError("kwargs must be a dict")
    if method not in ["sub2line", "line2sub"]:
        raise ValueError("Unknown method to build transmission network")

    # Load input data
    hifld_substations = get_hifld_electric_substations(const.blob_paths["substations"])
    hifld_substations.set_index("ID", inplace=True)
    hifld_lines = get_hifld_electric_power_transmission_lines(
        const.blob_paths["transmission_lines"]
    )
    hifld_lines.set_index("ID", inplace=True)
    hifld_data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    hifld_zones = get_zone(os.path.join(hifld_data_dir, "zone.csv"))  # noqa: F841

    # Filter substations based on their `LINES` attribute, check for location dupes
    substations = filter_substations_with_zero_lines(hifld_substations)
    check_for_location_conflicts(substations)

    if method == "sub2line":
        print("filter lines based on substations")
        print("---------------------------------")
        lines = filter_lines_with_unavailable_substations(hifld_lines)
        lines = filter_lines_with_no_matching_substations(lines, substations)
        lines = filter_lines_with_nonmatching_substation_coords(lines, substations)
        lines = filter_lines_with_identical_substation_names(lines)
    elif method == "line2sub":
        print("filter substations based on lines")
        print("---------------------------------")
        lines, substations = map_lines_to_substations_using_coords(
            substations, hifld_lines, **kwargs
        )

    # Add voltages to lines with missing data
    augment_line_voltages(lines, substations)

    return lines, substations
