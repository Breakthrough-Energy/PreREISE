import itertools
import json
import os
import tempfile
from io import BytesIO
from urllib.parse import urlparse
from urllib.request import urlopen
from zipfile import ZipFile

import networkx as nx
import pandas as pd
from tqdm import tqdm

from prereise.gather.griddata.hifld.const import abv2state  # noqa: F401
from prereise.gather.griddata.hifld.const import (
    contiguous_us_bounds,
    heat_rate_estimation_columns,
)
from prereise.gather.helpers import angular_distance, latlon_to_xyz


def get_eia_form_860(path):
    """Read the a CSV file for EIA Form 860 and keep plants located in contiguous
    states.

    :param str path: path to file. Either local or URL.
    :return: (*pandas.DataFrame*) -- operational power plant in contiguous states.
    """
    data = pd.read_csv(path)
    return data.query("State in @abv2state")


def get_eia_epa_crosswalk(path):
    """Read a CSV file mapping EIA plants IDs to EPA plant IDs, keep non-retired plants.

    :param str path: path to file. Either local or URL.
    :return: (*pandas.DataFrame*) -- filtered data frame.
    """
    crosswalk_match_exclude = {"CAMD Unmatched", "Manual CAMD Excluded"}  # noqa: F841
    data = (
        pd.read_csv(path)
        .query(
            "MATCH_TYPE_GEN not in @crosswalk_match_exclude and CAMD_STATUS != 'RET'"
        )
        .astype(
            {
                "MOD_EIA_PLANT_ID": int,
                "MOD_CAMD_UNIT_ID": "string",
                "MOD_CAMD_GENERATOR_ID": "string",
                "MOD_EIA_GENERATOR_ID_GEN": "string",
            }
        )
    )
    return data


def get_epa_ampd(path, years={2019}, cache=False):
    """Read a collection of zipped CSV files from the EPA AMPD dataset and keep readings
    from plants located in contiguous states.

    :param str path: path to folder. Either local or URL.
    :param iterable years: years of data to read (will be present in filenames).
    :param bool cache: Whether to locally cache the EPA AMPD data, and read from the
        cache when it's available.
    :return: (*pandas.DataFrame*) -- readings from operational power plant in contiguous
        states.
    """
    # Determine whether paths should be joined with os separators or URL separators
    try:
        result = urlparse(path)
        if result.scheme in {"http", "ftp", "s3", "file"}:
            path_sep = "/"
        else:
            path_sep = os.path.sep
    except Exception:
        raise ValueError(f"Could not interpret path {path}")
    # Trim trailing slashes as necessary to ensure that join works
    path = path.rstrip("/\\")

    # Build cache path if necessary
    if cache:
        cache_dir = os.path.join(os.path.dirname(__file__), "cache")
        os.makedirs(cache_dir, exist_ok=True)

    data = {year: {state: {} for state in abv2state} for year in years}
    for year in sorted(years):
        for state in tqdm(abv2state):
            for month_num in range(1, 13):
                filename = f"{year}{state.lower()}{str(month_num).rjust(2, '0')}.zip"
                if cache:
                    try:
                        df = pd.read_csv(
                            os.path.join(cache_dir, filename),
                            usecols=heat_rate_estimation_columns,
                        )
                    except Exception:
                        df = pd.read_csv(
                            path_sep.join([path, filename]),
                            usecols=heat_rate_estimation_columns,
                        )
                        df.to_csv(
                            os.path.join(cache_dir, filename),
                            compression={
                                "method": "zip",
                                "archive_name": filename.replace(".zip", ".csv"),
                            },
                        )
                else:
                    df = pd.read_csv(
                        path_sep.join([path, filename]),
                        usecols=heat_rate_estimation_columns,
                    )
                data[year][state][month_num] = df
    joined = pd.concat(
        [
            data[year][state][month_num]
            for year in sorted(years)
            for state in abv2state
            for month_num in range(1, 13)
        ]
    )

    return joined.astype({"UNITID": "string"})


def get_epa_needs(path):
    """Read the a CSV file for an EPA NEEDS dataset and keep plants located in
    contiguous states.

    :param str path: path to file. Either local or URL.
    :return: (*pandas.DataFrame*) -- operational power plant in contiguous states.
    """
    data = pd.read_csv(path)
    return data.query("`State Name` in @abv2state.values()")


def get_hifld_power_plants(path):
    """Read the HIFLD Power Plants CSV file and keep operational plants located in
    contiguous states.

    :param str path: path to file. Either local or URL.
    :return: (*pandas.DataFrame*) -- operational power plant in contiguous states.
    """
    data = (
        pd.read_csv(path)
        .astype(
            {
                "SOURCEDATE": "datetime64",
                "VAL_DATE": "datetime64",
            }
        )
        .rename(columns={"SOURC_LONG": "SOURCE_LON"})
        .drop(columns=["OBJECTID"])
    )
    return data.query("STATUS == 'OP' and STATE in @abv2state")


def get_hifld_generating_units(path):
    """Read the HIFLD Generating Units CSV file and keep operational plants located in
    contiguous states.

    :param str path: path to file. Either local or URL.
    :return: (*pandas.DataFrame*) -- operational generating units in contiguous states.
    """
    data = (
        pd.read_csv(path)
        .astype({"SOURCEDATE": "datetime64"})
        .drop(columns=["OBJECTID"])
    )
    return data.query("STATUS == 'OP' and STATE in @abv2state")


def get_hifld_electric_substations(path):
    """Read the HIFLD Electric Substations CSV file and keep in service substations
    located in contiguous states and connected to at least one transmission line.

    :param str path: path to file. Either local or URL.
    :return: (*pandas.DataFrame*) -- in service electric substations in contiguous
        states that are connected to at least one electric power transmission line.
    """
    data = (
        pd.read_csv(path)
        .drop(columns=["OBJECTID"])
        .round({"MAX_VOLT": 3, "MIN_VOLT": 3})
    )

    return data.query(
        "(STATUS == 'IN SERVICE' or STATUS == 'NOT AVAILABLE') and STATE in @abv2state"
    )


def _join_line_segments(segments, threshold=0.001):
    """Given a list of line segments, join them together as best as possible.

    :param list segments: list of segments, each defined as a list of (lon, lat)
        coordinate pairs.
    :param float threshold: minimum angular distance for a segment to be considered.
        Defined as the angular distance from the segment start to segment end (degrees).
    :return: (*list*) -- consolidated list of points.
    """

    def _generate_linear_spanning_tree(segments):
        """Given a list of segments, create a minimum spanning tree and ensure that it
        is linear (i.e. there are two nodes of degree 1, all other nodes are degree 2).

        :param list segments: list of segments, each defined as a list of (lon, lat)
            coordinate pairs.
        :return: (*networkx.Graph*) -- a minimum spanning tree from the segments.
        :raises ValueError: if the minimum spanning tree is not linear
        """
        # Build a Graph representing the existing connections between segment endpoints
        g = nx.Graph()
        # add a 'start' and 'end' node for each segment, and a zero-cost edge b/w them
        for i in range(len(segments)):
            g.add_edge((i, "start"), (i, "end"), weight=0)
        # Add edge weights by the angular distance between different segment endpoints
        for (seg1, which1), (seg2, which2) in itertools.combinations(g.nodes, 2):
            if seg1 == seg2:
                # no edge needed, since there's already a zero-cost edge there
                continue
            # Extract latitude and longitude from the appropriate end of each segment
            lon1, lat1 = segments[seg1][0 if which1 == "start" else -1]
            lon2, lat2 = segments[seg2][0 if which2 == "start" else -1]
            edge_angle = angular_distance(
                latlon_to_xyz(lat1, lon1), latlon_to_xyz(lat2, lon2)
            )
            g.add_edge((seg1, which1), (seg2, which2), weight=edge_angle)
        # Identify edges to connect the segments
        tree = nx.algorithms.tree.minimum_spanning_tree(g)
        # Ensure that the minimum spanning tree is linear
        if max(dict(nx.degree(tree)).values()) > 2:
            raise ValueError("The minimum spanning tree isn't linear")
        return tree

    if len(segments) == 1:
        # There's only one segment in the list, so no joining is necessary
        return segments[0]

    segments_df = pd.Series(segments).to_frame(name="segments")
    segments_df["distance"] = segments_df["segments"].map(
        lambda x: angular_distance(
            latlon_to_xyz(x[0][1], x[0][0]),  # first point
            latlon_to_xyz(x[-1][1], x[-1][0]),  # last point
        )
    )
    filtered_segments = segments_df.loc[segments_df["distance"] > threshold]
    if len(filtered_segments) == 1:
        # There's only one segment left in the list, so no joining is necessary
        return filtered_segments["segments"].iloc[0]

    # Sort the segments by length, in case the minimum spanning tree isn't linear
    sorted_segments = filtered_segments.sort_values("distance")
    # Make a minimum spanning tree, dropping small segments as necessary for linearity
    for i in range(len(sorted_segments)):
        try:
            linear_segments = sorted_segments.iloc[i:]["segments"].tolist()
            tree = _generate_linear_spanning_tree(linear_segments)
            # We found a good minimum spanning tree, so we can exit
            break
        except ValueError:
            # The minimum spanning tree wasn't good, go to the next iteration
            pass

    # Identify an endpoint of the linear minimum spanning tree
    node_degrees = dict(nx.degree(tree))
    endpoint = min(k for k, v in node_degrees.items() if v == 1)
    # Traverse the tree, adding segments in order
    joined_segments = []
    traversal = nx.algorithms.traversal.dfs_edges(tree, source=endpoint)
    for (seg1, which1), (seg2, _) in traversal:
        if seg1 == seg2:
            if which1 == "start":
                joined_segments += linear_segments[seg1]
            else:
                joined_segments += linear_segments[seg1][::-1]

    return joined_segments


def get_hifld_electric_power_transmission_lines(path):
    """Read the HIFLD Electric Power Transmission Lines json zip file and keep in
    service lines.

    :param str path: path to zip file. Either local or URL.
    :return: (*pandas.DataFrame*) -- each element is a dictionary enclosing the
        information of the electric power transmission line along with its topology.
    """
    dir = tempfile.TemporaryDirectory()
    if path[:4] == "http":
        with urlopen(path) as zipresp:
            with ZipFile(BytesIO(zipresp.read())) as zipfile:
                zipfile.extractall(os.path.join(dir.name, "topology"))
    else:
        with ZipFile(path, "r") as zipfile:
            zipfile.extractall(os.path.join(dir.name, "topology"))

    fp = os.path.join(dir.name, "topology", "Electric_Power_Transmission_Lines.geojson")
    with open(fp, "r", encoding="utf8") as f:
        data = json.load(f)
    dir.cleanup()

    properties = (
        pd.DataFrame([line["properties"] for line in data["features"]])
        .astype({"ID": "int64", "NAICS_CODE": "int64", "SOURCEDATE": "datetime64"})
        .drop(columns=["OBJECTID", "SHAPE_Length"])
        .round({"VOLTAGE": 3})
    )

    properties["COORDINATES"] = [
        line["geometry"]["coordinates"] for line in data["features"]
    ]

    # Join multiple distinct segments as necessary to get one single list
    properties["COORDINATES"] = properties["COORDINATES"].map(
        lambda x: _join_line_segments(x) if not isinstance(x[0][0], float) else x
    )

    # Flip [(lon, lat), (lon, lat), ..] points to [(lat, lon), (lat, lon), ...]
    properties["COORDINATES"] = properties["COORDINATES"].map(
        lambda x: [y[::-1] for y in x]
    )

    within_bounding_box = properties["COORDINATES"].apply(
        lambda x: (
            (contiguous_us_bounds["south"] < x[0][0] < contiguous_us_bounds["north"])
            & (contiguous_us_bounds["west"] < x[0][1] < contiguous_us_bounds["east"])
            & (contiguous_us_bounds["south"] < x[-1][0] < contiguous_us_bounds["north"])
            & (contiguous_us_bounds["west"] < x[-1][1] < contiguous_us_bounds["east"])
        )
    )
    properties = properties.loc[within_bounding_box]

    # Replace dummy data with explicit 'missing'
    properties.loc[properties.VOLTAGE == -999999, "VOLTAGE"] = pd.NA

    return properties.query("STATUS == 'IN SERVICE' or STATUS == 'NOT AVAILABLE'")


def get_transformer_parameters(
    data_dir=None, transformer_designs_path=None, impedance_ratios_path=None
):
    """Load transformer designs (by voltage pairs) and transformer impedance ratios
    (by higher voltage) and combine into a single dataframe.

    :param str data_dir: if this is not None, two files in this directory will be
        loaded: 'transformer_params.csv' and 'transformer_impedance_ratios.csv'.
        Required columns for each file are listed in the descriptions of
        the ``transformer_designs_path`` and ``impedance_ratios_path`` parameters.
    :param str transformer_designs_path: if ``data_dir`` is None, this file will be
        loaded. Required columns are 'low_kV', 'high_kV', 'x', and 'MVA'.
    :param str impedance_ratios_path: if ``data_dir`` is None, this file will be loaded.
        Required columns are 'high_kV' and 'x_to_r_ratio'.
    :raises TypeError: if ``data_dir`` is None and either of
        ``transformer_designs_path`` or ``impedance_ratios_path`` is None.
    :return: (*pandas.DataFrame*) -- index is (low_kV, high_kV), columns are 'x', 'r',
        and 'MVA'. 'x' and 'r' values are per-unit, 'MVA' is in megawatts.
    """
    if data_dir is None and (
        transformer_designs_path is None or impedance_ratios_path is None
    ):
        raise TypeError(
            "Either data_dir or transformer_designs_path and impedance_ratios_path "
            "must be specified."
        )
    if data_dir is not None:
        transformer_designs_path = os.path.join(data_dir, "transformer_params.csv")
        impedance_ratios_path = os.path.join(
            data_dir, "transformer_impedance_ratios.csv"
        )
    transformer_designs = pd.read_csv(transformer_designs_path)
    transformer_impedance_ratios = pd.read_csv(
        impedance_ratios_path, index_col="high_kV"
    )
    transformer_designs["r"] = transformer_designs["x"] / transformer_designs[
        "high_kV"
    ].map(transformer_impedance_ratios["x_to_r_ratio"])
    return transformer_designs.set_index(["low_kV", "high_kV"])[["x", "r", "MVA"]]


def get_zone(path):
    """Read zone CSV file.

    :param str path: path to file. Either local or URL.
    :return: (*pandas.DataFrame*) -- information related to load zone
    """
    return pd.read_csv(path, index_col="zone_id")


def get_us_counties(path):
    """Read the file containing county data.

    :param str path: path to file. Either local or URL.
    :return: (*pandas.DataFrame*) -- information related to counties
    """
    return pd.read_csv(path).set_index("county_fips")


def get_us_zips(path):
    """Read the file containing ZIP code data.

    :param str path: path to file. Either local or URL.
    :return: (*pandas.DataFrame*) -- information related to ZIP codes
    """
    return pd.read_csv(path, dtype={"zip": "string"}).set_index("zip")
