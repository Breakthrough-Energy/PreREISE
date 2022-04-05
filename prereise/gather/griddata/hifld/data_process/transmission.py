import math
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
from prereise.gather.griddata.hifld.data_process.topology import (
    add_interconnects_by_connected_components,
    get_mst_edges,
)
from prereise.gather.griddata.transmission import const as transmission_const
from prereise.gather.griddata.transmission.geometry import (
    Conductor,
    ConductorBundle,
    Line,
    PhaseLocations,
    Tower,
)
from prereise.gather.griddata.transmission.helpers import (
    calculate_z_base,
    translate_to_per_unit,
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


def map_lines_to_substations_using_coords(
    substations, lines, rounding=3, drop_zero_distance_line=True
):
    """Map lines to substations using coordinates.

    :param pandas.DataFrame substations: data frame of substations.
    :param pandas.DataFrame lines: data frame of all lines.
    :param int rounding: number of digits in coordinates rounded up to.
    :param bool drop_zero_distance_line: drop zero distance line or not, defaults to
        True.
    :return: (*tuple*) -- lines and substations data frame.
    :raises TypeError: if rounding is not an integer.
    """
    if not isinstance(rounding, int):
        raise TypeError("rounding must be an integer")

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
            set(line2sub.loc[line2sub[e_sub].isna(), e].map(tuple))
            for e, e_sub in end_sub.items()
        ]
    )
    tree = KDTree([ll2uv(p[1], p[0]) for p in subcoord])
    endpoint2neighbor = {
        p: subcoord2subid[subcoord[tree.query(ll2uv(p[1], p[0]))[1]]]
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
        for t in ["SUBSTATION", "TAP", "RISER", "DEAD END", "NOT AVAILABLE"]:
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

    # Remove lines which ended up assigned to the same substation after consolidation
    if drop_zero_distance_line:
        idx = new_lines["SUB_1_ID"].compare(new_lines["SUB_2_ID"]).index
        print(
            f"dropping {new_lines.shape[0] - len(idx)} lines having same endpoints "
            "after substation consolidation"
        )
        new_lines = new_lines.loc[idx]

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


def filter_islands_and_connect_with_mst(
    lines,
    substations,
    island_size_lower_bound=0,
    island_size_upper_bound=None,
    **kwargs,
):
    """Filter islands by user specific sizes and connect all islands with a minimum
    spanning tree.

    :param pandas.DataFrame lines: data frame of lines.
    :param pandas.DataFrame substations: data frame of substations.
    :param int island_size_lower_bound: smallest island the function should consider
        exclusively, defaults to 0.
    :param int island_size_upper_bound: largest island the function should consider
        exclusively, defaults to None, which includes all islands up to the largest one.
    :param \\*\\*kwargs: optional arguments for :py:func:`get_mst_edges`.
    :return: (*tuple*) -- modified lines and substations data frames, lines and
        substations in filtered islands are dropped and new lines from the minimum
        spanning tree among islands are added.
    :raises TypeError:
        if ``island_size_lower_bound`` is not int, and/or
        if ``island_size_upper_bound`` is not int.
    :raises ValueError:
        if ``island_size_lower_bound`` is greater or equal to
        ``island_size_upper_bound``.
    """
    if island_size_upper_bound is None:
        island_size_upper_bound = len(substations) + 1
    if not isinstance(island_size_lower_bound, int):
        raise TypeError("island_size_lower_bound must be an integer")
    if not isinstance(island_size_upper_bound, int):
        raise TypeError("island_size_upper_bound must be an integer")
    if island_size_lower_bound >= island_size_upper_bound:
        raise ValueError(
            "island_size_lower_bound must be smaller than island_size_upper_bound"
        )

    # Filter lines and substations based on island sizes
    graph = nx.convert_matrix.from_pandas_edgelist(lines, "SUB_1_ID", "SUB_2_ID")
    sub_to_drop = set().union(
        *[
            cc
            for cc in list(nx.connected_components(graph))
            if len(cc) <= island_size_lower_bound or len(cc) >= island_size_upper_bound
        ]
    )
    len_lines_before = len(lines)
    lines = lines.loc[~lines["SUB_1_ID"].isin(sub_to_drop)]
    print(
        f"dropping {len_lines_before - len(lines)} lines due to island size filtering"
    )
    len_substations_before = len(substations)
    substations.drop(sub_to_drop, inplace=True)
    print(
        f"dropping {len_substations_before - len(substations)} substations due to "
        f"island size filtering"
    )

    # Connect selected connected components
    mst_edges = get_mst_edges(lines, substations, **kwargs)

    first_new_id = lines.index.max() + 1
    new_lines = pd.DataFrame(
        [{"SUB_1_ID": x[2]["start"], "SUB_2_ID": x[2]["end"]} for x in mst_edges],
        index=pd.RangeIndex(first_new_id, first_new_id + len(mst_edges)),
    )
    new_lines = new_lines.assign(VOLTAGE=pd.NA, VOLT_CLASS="NOT AVAILABLE")
    new_lines["COORDINATES"] = new_lines.apply(
        lambda x: [
            [
                substations.loc[x.SUB_1_ID, "LATITUDE"],
                substations.loc[x.SUB_1_ID, "LONGITUDE"],
            ],
            [
                substations.loc[x.SUB_2_ID, "LATITUDE"],
                substations.loc[x.SUB_2_ID, "LONGITUDE"],
            ],
        ],
        axis=1,
    )
    lines = pd.concat([lines, new_lines])

    return lines, substations


def augment_line_voltages(
    lines,
    substations,
    volt_class_defaults=None,
    voltage_assumptions=None,
    state_threshold_100_161=0.95,
):
    """Fill in voltages for lines with missing voltages, using a series of heuristics.
    The ``lines`` dataframe will be modified in-place.

    :param pandas.DataFrame lines: data frame of lines.
    :param pandas.DataFrame substations: data frame of substations.
    :param dict/pandas.Series volt_class_defaults: mapping of volt classes to default
        replacement voltage values. If None, internally-defined defaults will be used.
    :param dict/pandas.Series voltage_assumptions: mapping of branches to voltages.
        If None, internally-defined defaults will be used.
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
            missing = lines.loc[lines["VOLTAGE"].isnull()]
            if len(missing) == 0:
                print(f"No more missing voltages remain after neighbor {method_name}")
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
    if voltage_assumptions is None:
        voltage_assumptions = const.line_voltage_assumptions

    # Set voltages based on per-branch information
    lines["VOLTAGE"].update(voltage_assumptions)
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
    buses.index.name = "bus_id"

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
        (b, volt_series.sort_values().index[i + 1])
        for sub, volt_series in bus.groupby("sub_id")["baseKV"]
        for i, b in enumerate(volt_series.sort_values().index[:-1])
        if len(volt_series) > 1
    ]

    return pd.DataFrame(bus_pairs, columns=["from_bus_id", "to_bus_id"])


def add_impedance_and_rating(branch, bus_voltages, line_overrides=None):
    """Estimate branch impedances and ratings based on voltage and length (for lines),
    and add these to the branch data frame (modified inplace).

    :param pandas.DataFrame branch: branch data table. Required columns are:
        'VOLTAGE' (in kV) and 'length' (in km).
    :param pandas.Series bus_voltages: mapping of bus IDs to voltages (kV).
    :param dict/pandas.Series line_overrides: keys/index are line IDs (corresponding to
        indices of the ``branch`` data frame), values are tuples of
        (voltage, number of circuits, number of conductors in bundle).
    """

    def build_tower(series):
        """Given a series of line design data, build a representative Tower.

        :param pandas.Series series: line data.
        :return: (*prereise.gather.griddata.transmission.geometry.Tower*) -- Tower.
        """
        conductor = Conductor(series["conductor"])
        bundle = ConductorBundle(
            conductor=conductor,
            n=series["bundle_count"],
            spacing=series["spacing"],
        )
        num_circuits = series["circuits"]
        locations = PhaseLocations(
            a=tuple(tuple(series[[f"a{i}x", f"a{i}y"]]) for i in range(num_circuits)),
            b=tuple(tuple(series[[f"b{i}x", f"b{i}y"]]) for i in range(num_circuits)),
            c=tuple(tuple(series[[f"c{i}x", f"c{i}y"]]) for i in range(num_circuits)),
            circuits=num_circuits,
        )
        return Tower(bundle=bundle, locations=locations)

    line_overrides = {} if line_overrides is None else line_overrides
    # Read designs
    designs_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "line_designs.csv"
    )
    tower_designs = pd.read_csv(designs_path)
    # Use design info to build object for further analysis
    tower_designs["Tower"] = tower_designs.apply(build_tower, axis=1)

    # The default line design for each voltage is single-circuit, smallest bundle
    default_designs = pd.Series(
        {
            voltage: (voltage, 1, group["bundle_count"].min())
            for voltage, group in tower_designs.groupby("voltage")
        }
    )
    # Find the default line design for each voltage
    closest_voltage_design = {
        v: default_designs.iloc[default_designs.index.get_loc(v, method="nearest")]
        for v in branch["VOLTAGE"].dropna().unique()
    }
    # Add meaningful index for easier lookups using design tuples
    tower_designs.set_index(["voltage", "circuits", "bundle_count"], inplace=True)
    # Map each transmission line to its corresponding Tower design
    branch_plus_lines = branch.assign(
        line_object=branch.query("type == 'Line'").apply(
            lambda x: Line(
                tower=tower_designs.loc[
                    line_overrides.get(x.name, closest_voltage_design[x["VOLTAGE"]]),
                    "Tower",
                ],
                voltage=x["VOLTAGE"],
                length=x["length"],
            ),
            axis=1,
        ),
    )

    default_thermal_ratings = (
        tower_designs.loc[default_designs]
        .reset_index()
        .set_index("voltage")
        .apply(
            lambda x: Line(tower=x["Tower"], voltage=x.name, length=1).thermal_rating,
            axis=1,
        )
    )
    # Now that we have Line objects for each Line, we can use the lower-level functions
    branch["x"] = branch_plus_lines.apply(
        lambda x: estimate_branch_impedance(x, bus_voltages), axis=1
    )
    branch["rateA"] = branch_plus_lines.apply(
        lambda x: estimate_branch_rating(x, bus_voltages, default_thermal_ratings),
        axis=1,
    )


def estimate_branch_impedance(branch, bus_voltages):
    """Estimate branch impedance using transformer voltages or line voltage and length.

    :param pandas.Series branch: data for a single branch (line or transformer). All
        branches require 'type' attributes, lines require 'VOLTAGE' and 'line_object',
        transformers require 'from_bus_id' and 'to_bus_id'.
    :param pandas.Series bus_voltages: mapping of buses to voltages.
    :return: (*float*) -- impedance for that branch (per-unit).
    """

    def _euclidian(a, b):
        return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** (1 / 2)

    if branch.loc["type"] == "Transformer":
        voltage_tuple = sorted(bus_voltages.loc[[branch.from_bus_id, branch.to_bus_id]])
        reactance_lookup = pd.Series(const.transformer_reactance)
        # Find the 'closest' voltage pair via Euclidian distance
        closest_voltage_tuple = (
            reactance_lookup.index.to_series()
            .map(lambda x: _euclidian(x, voltage_tuple))
            .idxmin()
        )
        return const.transformer_reactance[closest_voltage_tuple]
    elif branch.loc["type"] == "Line":
        z_base = calculate_z_base(v_base=branch["VOLTAGE"], s_base=const.s_base)
        return translate_to_per_unit(
            branch["line_object"].series_impedance.imag, "x", z_base
        )
    else:
        raise ValueError(f"{branch.loc['type']} not a valid branch type")


def calculate_branch_mileage(branch):
    """Estimate distance of a line.

    :param pandas.Series branch: data for a single line.
    :return: (*float*) -- distance (in miles) for that line.
    """
    coordinates = branch.loc["COORDINATES"]
    return sum([haversine(a, b) for a, b in zip(coordinates[:-1], coordinates[1:])])


def estimate_branch_rating(branch, bus_voltages, voltage_thermal_ratings):
    """Estimate branch rating using line voltage or constant value for transformers.

    :param pandas.Series branch: data for a single branch (line or transformer). All
        branches require 'type' attributes, lines require 'line_object'.
    :param pandas.Series bus_voltages: mapping of buses to voltages.
    :param pandas.Series voltage_thermal_ratings: line thermal ratings by voltage.
    :return: (*float*) -- rating for that branch (MW).
    :raises ValueError: if branch 'type' attribute not recognized.
    """
    if branch.loc["type"] == "Line":
        return branch["line_object"].power_rating
    elif branch.loc["type"] == "Transformer":
        rating = const.transformer_rating
        max_voltage = bus_voltages.loc[[branch.from_bus_id, branch.to_bus_id]].max()
        closest_voltage_rating = voltage_thermal_ratings.iloc[
            voltage_thermal_ratings.index.get_loc(max_voltage, method="nearest")
        ]
        num_addl_transformers = int(closest_voltage_rating / rating)
        return rating * (1 + num_addl_transformers)
    raise ValueError(f"{branch.loc['type']} not a valid branch type")


def split_lines_to_ac_and_dc(lines, dc_override_indices=None):
    """Given a data frame of mixed AC & DC lines, where some DC lines are not
    appropriately labeled, split into an AC data frame and a DC data frame.

    :param pandas.DataFrame lines: combined data frame of AC & DC lines.
    :param iterable dc_override_indices: indices to coerce to DC classification.
    :return: (*tuple*) -- two data frames, of AC & DC lines, respectively.
    """
    if dc_override_indices is None:
        dc_override_indices = {}
    dc_types = {"DC; OVERHEAD", "DC; UNDERGROUND"}  # noqa: F841
    dc_lines = lines.query("TYPE in @dc_types or index in @dc_override_indices")
    ac_lines = lines.query("index not in @dc_lines.index")
    return ac_lines.copy(), dc_lines.copy()


def add_b2bs_to_dc_lines(dc_lines, substations, b2b_ratings):
    """Given back-to-back (B2B) converter station ratings, add entries to the DC lines
    table (modified inplace) representing the HVDC links between interconnections.

    :param pandas.DataFrame dc_lines: table of HVDC line information.
    :param pandas.DataFrame substations: table of substation information.
    :param dict/pandas.Series b2b_capacities: capacities of B2B HVDC facilties. Keys are
        strings which are containined within exactly two substation 'NAME' properties
        (one on either 'side' of an interconnection seam), values are B2B facilitiy
        capacity in MW.
    :raises ValueError: if a given B2B capacity name does not identify exactly two
        substations.
    """
    # Check all lines and build dict of lines to be added (if validation passes)
    to_add = []
    for name, rating in b2b_ratings.items():
        sub_ids = substations.loc[substations["NAME"].str.contains(f"{name}_")].index
        if len(sub_ids) != 2:
            raise ValueError(f"Could not identify two substations for B2B: {name}")
        to_add.append({"SUB_1_ID": sub_ids[0], "SUB_2_ID": sub_ids[1], "Pmax": rating})

    # Now that we know all are good, loop through and append to extend DC lines inplace
    # The first new ID is calculated to not share a leading digit with existing DC lines
    prev_max = dc_lines.index.max()
    order_of_magnitude = 10 ** (int(math.log10(prev_max)))
    first_new_id = order_of_magnitude * int(prev_max / order_of_magnitude + 1)
    # We need to loop through and add one-by-one to be able to append inplace
    for i, info in enumerate(to_add):
        dc_lines.loc[first_new_id + i] = pd.Series(info)


def assign_buses_to_lines(ac_lines, dc_lines, bus):
    """Map substation IDs to bus IDs for AC & DC lines. Within the ``bus`` table, each
    unique 'sub_id' should have one bus per connected voltage level; AC lines map
    uniquely based on their 'VOLTAGE' attribute, while DC lines are mapped to the
    highest-voltage bus within each substation. Both are modified inplace.

    :param pandas.DataFrame ac_lines: data frame containing at least
        'SUB_1_ID' and 'SUB_2_ID' columns.
    :param pandas.DataFrame dc_lines: data frame containing at least
        'SUB_1_ID' and 'SUB_2_ID' columns.
    :param pandas.DataFrame bus: data frame containing at least 'sub_id' and 'baseKV'
        columns, with an index named 'bus_id'.
    """
    # Create pandas Series that can be used for quick lookups
    reindexed = bus.reset_index()
    sub_and_voltage_to_bus = reindexed.set_index(["sub_id", "baseKV"])["bus_id"]
    highest_voltage = reindexed.sort_values("baseKV").groupby("sub_id").last()["bus_id"]
    # Use mappings to fill bus IDs
    ac_lines["from_bus_id"] = ac_lines.apply(
        lambda x: sub_and_voltage_to_bus.loc[(x["SUB_1_ID"], x["VOLTAGE"])], axis=1
    )
    ac_lines["to_bus_id"] = ac_lines.apply(
        lambda x: sub_and_voltage_to_bus.loc[(x["SUB_2_ID"], x["VOLTAGE"])], axis=1
    )
    dc_lines["from_bus_id"] = dc_lines["SUB_1_ID"].map(highest_voltage)
    dc_lines["to_bus_id"] = dc_lines["SUB_2_ID"].map(highest_voltage)


def add_substation_info_to_buses(bus, substations, zones):
    """Using information looked up from substations and defined zones, add 'zone_id' and
    'interconnect' columns to the ``bus`` table (modified in-place).

    :param pandas.DataFrame bus: table of bus data, including 'sub_id' column.
    :param pandas.DataFrame substations: table of substation data, including 'STATE' and
        'interconnect' columns.
    :param pandas.DataFrame zones: table of zone data, including 'state' and
        'interconnect' columns, with an index named 'zone_id'.
    """
    zone_lookup = zones.reset_index().set_index(["state", "interconnect"])["zone_id"]
    zone_lookup.sort_index(inplace=True)  # unsorted MultiIndices have poor performance
    states = bus["sub_id"].map(substations["STATE"]).map(const.abv2state)
    bus["interconnect"] = bus["sub_id"].map(substations["interconnect"])
    bus["zone_id"] = bus.apply(
        lambda x: zone_lookup.loc[(states.loc[x.name], x.interconnect)],
        axis=1,
    )


def build_transmission(method="line2sub", **kwargs):
    """Build transmission network

    :param str method: method used to build network. Default method is *sub2line*
        where all substations are considered and lines are filtered accordingly. Other
        method is *line2sub* where all lines are considered and a list of substations
        is compiled.
    :param \\*\\*kwargs: keyword arguments to be passed to lower level functions,
        including :py:func:`map_lines_to_substations_using_coords` and
        :py:func:`get_mst_edges`.
    :raises TypeError: if ``method`` is not a str.
    :raises ValueError: if ``method`` is unknown.
    :return: (*tuple*) -- four data frames:
        AC branches, buses, substations, and DC lines, respectively.
    """
    if not isinstance(method, str):
        raise TypeError("method must be a str")
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
    hifld_substations.loc[const.substations_lines_filter_override, "LINES"] = None
    substations = filter_substations_with_zero_lines(hifld_substations)
    check_for_location_conflicts(substations)
    # Append the proxy substations to the source data
    substations = pd.concat([substations, pd.DataFrame(const.proxy_substations)])
    substations.index.name = "ID"

    # Filter out keyword arguments for filter_islands_and_connect_with_mst function
    island_kwargs = dict()
    for keyword in {
        "island_size_lower_bound",
        "island_size_upper_bound",
        "state_neighbor",
        "min_dist_method",
        "cost_metric",
        "memory_efficient",
        "kdtree_kwargs",
    }:
        if keyword in kwargs:
            island_kwargs[keyword] = kwargs.pop(keyword)

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

    lines, substations = filter_islands_and_connect_with_mst(
        lines, substations, **island_kwargs
    )

    # Separate DC lines from AC line processing, add ratings
    ac_lines, dc_lines = split_lines_to_ac_and_dc(lines, const.dc_line_ratings.keys())
    dc_lines["Pmax"] = dc_lines.index.to_series().map(const.dc_line_ratings)
    dc_lines["Pmin"] = -1 * dc_lines["Pmax"]

    # Add interconnect information to lines and substations via topology analysis
    add_interconnects_by_connected_components(
        ac_lines,
        substations,
        set().union(*const.seams_substations.values()),
        const.substation_interconnect_assumptions,
        const.line_interconnect_assumptions,
        const.interconnect_size_rank,
    )
    # use substation interconnects to label DC lines
    dc_lines["from_interconnect"] = dc_lines.SUB_1_ID.map(substations.interconnect)
    dc_lines["to_interconnect"] = dc_lines.SUB_2_ID.map(substations.interconnect)
    # Now that substations are split across interconnects, we can add B2B facilities
    add_b2bs_to_dc_lines(dc_lines, substations, const.b2b_ratings)

    # Add voltages to lines with missing data
    augment_line_voltages(ac_lines, substations)

    # Create buses from lines
    bus = create_buses(ac_lines)
    assign_buses_to_lines(ac_lines, dc_lines, bus)
    add_substation_info_to_buses(bus, substations, hifld_zones)

    # Add transformers, and calculate rating and impedance for all branches
    transformers = create_transformers(bus)
    transformers["type"] = "Transformer"
    transformers["interconnect"] = transformers["from_bus_id"].map(bus["interconnect"])
    first_new_id = ac_lines.index.max() + 1
    transformers.index = pd.RangeIndex(first_new_id, first_new_id + len(transformers))
    ac_lines["type"] = "Line"
    ac_lines["length"] = (
        ac_lines.apply(calculate_branch_mileage, axis=1)
        * transmission_const.kilometers_per_mile
    )
    branch = pd.concat([ac_lines, transformers])
    add_impedance_and_rating(branch, bus["baseKV"], const.line_design_assumptions)

    # Update substation max & min voltages using bus data (from lines)
    substations["MAX_VOLT"].update(bus.groupby("sub_id")["baseKV"].apply(max))
    substations["MIN_VOLT"].update(bus.groupby("sub_id")["baseKV"].apply(min))

    # Rename columns to match PowerSimData expectations
    branch.rename({"type": "branch_device_type"}, axis=1, inplace=True)
    substations.rename(
        {"NAME": "name", "LATITUDE": "lat", "LONGITUDE": "lon"}, axis=1, inplace=True
    )
    substations["interconnect_sub_id"] = substations.groupby("interconnect").cumcount()
    substations.index.name = "sub_id"

    return branch, bus, substations, dc_lines
