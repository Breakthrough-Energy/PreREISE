import hashlib
import os
import pickle
from itertools import combinations, product

import networkx as nx
import pandas as pd
from powersimdata.utility.distance import haversine, ll2uv
from scipy.spatial import KDTree
from tqdm import tqdm

from prereise.gather.griddata.hifld.const import abv_state_neighbor


def min_dist_of_2_conn_comp(
    nodes1, nodes2, dist_metric=haversine, memory_efficient=False
):
    """Calculate the minimum distance of two connected components based on the given
    distance metric.

    :param pandas.DataFrame nodes1: a data frame contains all the nodes of the first
        connected component with index being node ID and two columns being latitude
        and longitude in order.
    :param pandas.DataFrame nodes2: a data frame contains all the nodes of the second
        connected component with index being node ID and two columns being latitude
        and longitude in order.
    :param func dist_metric: a function defines the distance metric, defaults to
        :py:func:`haversine`.
    :param bool memory_efficient: run the function in a memory efficient way or not,
        defaults to False.
    :return: (*tuple*) -- a tuple contains three elements, the minimum distance
        follows by a pair of nodes from the two connected components respectively
        in order
    """
    if memory_efficient:
        min_dist = float("inf")
        for v1, v2 in product(nodes1.index, nodes2.index):
            tmp_dist = dist_metric(nodes1.loc[v1], nodes2.loc[v2])
            if tmp_dist < min_dist:
                min_dist, res_v1, res_v2 = tmp_dist, v1, v2
    else:
        distances = nodes1.apply(
            lambda x: nodes2.apply(lambda y: dist_metric(x, y), axis=1), axis=1
        )
        res_v1 = distances.min(axis=1).idxmin()
        res_v2 = distances.loc[res_v1].idxmin()
        min_dist = distances.loc[res_v1, res_v2]
    return min_dist, res_v1, res_v2


def min_dist_of_2_conn_comp_kdtree(nodes1, nodes2, **kwargs):
    """Calculate the minimum distance of two connected components using KDTree.

    :param pandas.DataFrame nodes1: a data frame contains all the nodes of the first
        connected component with index being node ID and two columns being latitude
        and longitude in order.
    :param pandas.DataFrame nodes2: a data frame contains all the nodes of the second
        connected component with index being node ID and two columns being latitude
        and longitude in order.
    :param \\*\\*kwargs: optional arguments for KDTree query.
    :return: (*tuple*) -- a tuple contains three elements, the minimum distance
        follows by a pair of nodes from the two connected components respectively
        in order

    .. note:: The minimum distance returned by this function depends on the
        configuration of KDTree by the user specified keyword arguments, Euclidean
        distance is used by default. See
        https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.KDTree.query.html#scipy.spatial.KDTree.query
        for more information.
    """
    swap = False
    if len(nodes1) < len(nodes2):
        nodes1, nodes2 = nodes2, nodes1
        swap = True
    tree = KDTree([ll2uv(p[1], p[0]) for p in nodes1.values])
    shortest_link = nodes2.apply(
        lambda x: tree.query(ll2uv(*x[::-1]), **kwargs), axis=1
    )
    min_dist, sub1_ind = shortest_link.min()
    sub1 = nodes1.index[sub1_ind]
    sub2 = shortest_link.loc[shortest_link == (min_dist, sub1_ind)].index[0]
    return (min_dist, sub2, sub1) if swap else (min_dist, sub1, sub2)


def find_adj_state_of_2_conn_comp(cc1, cc2, state_adj, subs):
    """Find the adjacent states between two given connected components.

    :param int/iterable cc1: substation ids of the first connected component
    :param int/iterable cc2: substation ids of the second connected component
    :param dict state_adj: a dictionary defines state neighbors, keys are state
        abbreviations, values are list of neighbor state abbreviations.
    :param pandas.DataFrame subs: substation data frame indexed by substation ids,
        contains a ``STATE`` column that defines the state of each substation.
    :return: (*tuple*) -- a pair of sets represents states within each connected
        component that are adjacent to the other one.
    """
    cc1_all_state = set(subs.loc[cc1].STATE.unique())
    cc2_all_state = set(subs.loc[cc2].STATE.unique())
    cc1_neighbors = cc1_all_state.union(*[set(state_adj[s]) for s in cc1_all_state])
    cc2_neighbors = cc2_all_state.union(*[set(state_adj[s]) for s in cc2_all_state])
    cc1_adj = cc2_neighbors & cc1_all_state
    cc2_adj = cc1_neighbors & cc2_all_state
    return cc1_adj, cc2_adj


def connect_islands_with_minimum_cost(
    lines,
    subs,
    state_neighbor=None,
    min_dist_method="naive",
    **kwargs,
):
    """Connect a group of islands defined by lines and substations into one big
    island with minimum cost.

    :param pandas.DataFrame lines: line data frame indexed by ``ID`` with two columns
        ``SUB_1_ID`` and ``SUB_2_ID`` representing the corresponding substations at the
        start and end points.
    :param pandas.DataFrame subs: substation data frame indexed by ``ID`` with two
        columns ``LATITUDE`` and ``LONGITUDE`` representing the geographical
        coordination of each entry.
    :param dict state_neighbor: a dictionary defines the adjacency relationship among
        states, defaults to None and the constant dictionary ``abv_state_neighbor``
        defined in the ``const`` module is used.
    :param func min_dist_method: the function used to calculate minimum distance
        between two connected components, defaults to *naive* which uses
        :py:func:`min_dist_of_2_conn_comp` or *kdtree* which uses
        :py:func:`min_dist_of_2_conn_comp_kdtree`.
    :param \\*\\*kwargs: keyword arguments to pass to either
        :py:func:`min_dist_of_2_conn_comp` or :py:func:`min_dist_of_2_conn_comp_kdtree`
        specified by ``min_dist_method``.
    :return: (*tuple*) -- a pair of lists, the first one is a list of all potential
        line candidates among given connected components; the second one is a list
        of subsequence of the first entry, representing the chosen lines to form a
        minimum spanning tree. Each entry of both lists is a 3-tuple, index of the
        first connected component, index of the second connected component,
        a dictionary with keys containing ``start``, ``end`` and ``weight``, defines
        the ``from substation ID``, ``to substation ID`` and the weight of the line
        calculated by either ``dist_metric`` or KDTree configurations defined in
        ``kwargs``.
    :raises ValueError: if ``min_dist_method`` is unknown.

        .. note:: the indexes of connected components are defined by the size,
            i.e. number of nodes, of the connected components in descending order.
    """

    if state_neighbor is None:
        state_neighbor = abv_state_neighbor

    # Construct a networkx graph using lines data frame
    graph = nx.convert_matrix.from_pandas_edgelist(lines, "SUB_1_ID", "SUB_2_ID")

    # Get the full list of connected components of the resultant graph sored by size in
    # ascending order
    all_cc = sorted(list(nx.connected_components(graph)), key=len, reverse=True)

    # Loop through all the combinations of connected components to identify potential
    # edges filtered by the adjacency relationship specified by the user
    edge_list = []
    for ind1, ind2 in tqdm(combinations(range(len(all_cc)), r=2)):
        cc1 = all_cc[ind1]
        cc2 = all_cc[ind2]
        # Find the adjacency states within the two connected components against each
        # other
        cc1_adj, cc2_adj = find_adj_state_of_2_conn_comp(cc1, cc2, state_neighbor, subs)
        if len(cc1_adj) > 0:
            nodes1 = subs.loc[cc1].query("STATE in @cc1_adj")[["LATITUDE", "LONGITUDE"]]
            nodes2 = subs.loc[cc2].query("STATE in @cc2_adj")[["LATITUDE", "LONGITUDE"]]
            # Run an exhaustive search on the filtered substations of both connected
            # components to find a line with minimum cost the connects the two islands
            if min_dist_method == "kdtree":
                min_dist, sub1, sub2 = min_dist_of_2_conn_comp_kdtree(
                    nodes1, nodes2, **kwargs
                )
            elif min_dist_method == "naive":
                min_dist, sub1, sub2 = min_dist_of_2_conn_comp(nodes1, nodes2, **kwargs)
            else:
                raise ValueError("min_dist_method must be either `naive` or `kdtree`")
            edge_list.append(
                (ind1, ind2, {"weight": min_dist, "start": sub1, "end": sub2})
            )
    # Build a minimum spanning tree based on the weighted edge list
    cc_graph = nx.Graph()
    cc_graph.add_edges_from(edge_list)
    cc_mst = nx.minimum_spanning_tree(cc_graph)
    return edge_list, sorted(cc_mst.edges(data=True))


def get_mst_edges(lines, substations, **kwargs):
    """Get the set of lines which connected the connected components of the lines graph,
    either from a cache or by generating from scratch and caching.

    :param pandas.DataFrame lines: data frame of lines.
    :param pandas.DataFrame substations: data frame of substations.
    :param \\*\\*kwargs: optional arguments for
        :py:func:`connect_islands_with_minimum_cost`.
    :return: (*list*) -- each entry is a 3-tuple:
        index of the first connected component (int),
        index of the second connected component (int),
        a dictionary with keys containing ``start``, ``end`` and ``weight``, defines
        the ``from substation ID``, ``to substation ID`` and the distance of the line.
    """
    cache_dir = os.path.join(os.path.dirname(__file__), "cache")
    os.makedirs(cache_dir, exist_ok=True)
    cache_key = (
        repr(lines[["SUB_1_ID", "SUB_2_ID"]].to_numpy().tolist())
        + repr(substations[["LATITUDE", "LONGITUDE"]].to_numpy().tolist())
        + repr(kwargs)
    )
    cache_hash = hashlib.md5(cache_key.encode("utf-8")).hexdigest()
    try:
        with open(os.path.join(cache_dir, f"mst_{cache_hash}.pkl"), "rb") as f:
            print("Reading cached minimum spanning tree")
            mst_edges = pickle.load(f)
    except Exception:
        print("No minimum spanning tree available, generating...")
        _, mst_edges = connect_islands_with_minimum_cost(lines, substations, **kwargs)
        with open(os.path.join(cache_dir, f"mst_{cache_hash}.pkl"), "wb") as f:
            pickle.dump(mst_edges, f)
    return mst_edges


def add_interconnects_by_connected_components(
    lines,
    substations,
    seams_substations,
    substation_assumptions,
    line_assumptions,
    interconnect_size_rank,
):
    """Disconnect a large connected component using a set of connecting substations,
    label the resulting connected components, then reconnect dropped lines and
    substations, using explicit assumptions plus inference from neighboring lines. The
    ``lines`` and ``substations`` data frames are modified inplace with a new
    'interconnect' column.

    :param pandas.DataFrame lines: data frame of line information.
    :param pandas.DataFrame substations: data frame of substation information.
    :param iterable seams_substations: IDs of substations to drop.
    :param dict substation_assumptions: labeling assumptions for substations.
    :param dict line_assumptions: labeling assumptions for lines.
    :param iterable interconnect_size_rank: ordered iterable of interconnection names.
    :raises ValueError: if at least one dropped line's interconnection isn't specified
        and can't be inferred from its neighbors, or if the final number of connected
        components don't match the length of the ``interconnect_size_rank``.
    """
    # Create a graph of the network, and drop lines based on substations
    dropped_lines = lines.loc[
        lines["SUB_1_ID"].isin(seams_substations)
        | lines["SUB_2_ID"].isin(seams_substations)
    ]
    g = nx.convert_matrix.from_pandas_edgelist(lines, "SUB_1_ID", "SUB_2_ID")
    g.remove_nodes_from(seams_substations)
    # Label interconnections based on their sizes
    sorted_interconnects = sorted(nx.connected_components(g), key=len)[::-1]
    labels = pd.Series("unknown", index=lines.index, dtype="string")
    for i, name in enumerate(interconnect_size_rank):
        labels.loc[lines.SUB_1_ID.isin(sorted_interconnects[i])] = name
    labels.loc[dropped_lines.index] = "dropped"
    # Label some dropped lines and unknown interconnection lines (small islands)
    for interconnect, sub_ids in substation_assumptions.items():
        labels.loc[
            lines["SUB_1_ID"].isin(sub_ids) | lines["SUB_2_ID"].isin(sub_ids),
        ] = interconnect
    for interconnect, line_ids in line_assumptions.items():
        labels.loc[line_ids] = interconnect
    # Use neighboring lines at non-dropped substations to infer line interconnections
    dropped_lines = lines.loc[labels == "dropped"]
    non_dropped_lines = lines.loc[labels != "dropped"]
    for id, line in dropped_lines.iterrows():
        non_dropped_sub = (  # noqa: F841
            line.SUB_1_ID if line.SUB_2_ID in seams_substations else line.SUB_2_ID
        )
        other_lines = non_dropped_lines.query(
            "SUB_1_ID == @non_dropped_sub or SUB_2_ID == @non_dropped_sub"
        )
        other_line_interconnects = labels.loc[other_lines.index].unique()
        if len(other_line_interconnects) != 1:
            raise ValueError(f"Couldn't infer interconnection for line {id}")
        labels.loc[id] = other_line_interconnects[0]
    lines["interconnect"] = labels

    # When lines of multiple interconnections meet at a substation, split it
    for sub_id in sorted(seams_substations):
        # Find all lines disconnected by removing this substation
        sub_dropped_lines = lines.query("SUB_1_ID == @sub_id or SUB_2_ID == @sub_id")
        # Find interconnects for dropped lines which have been successfully labeled
        new_sub_interconnects = sub_dropped_lines["interconnect"].unique()
        # Build new substations to replace the old one
        first_new_sub_id = substations.index.max() + 1
        new_substations = pd.concat(
            [substations.loc[sub_id]] * len(new_sub_interconnects), axis=1
        ).T
        new_substations.index = pd.RangeIndex(
            first_new_sub_id, first_new_sub_id + len(new_sub_interconnects)
        )
        new_substations["NAME"] = [
            substations.loc[sub_id, "NAME"] + f"_{i}" for i in new_sub_interconnects
        ]
        # Add these new substations to the existing ones
        for new_id, new_substation in new_substations.iterrows():
            substations.loc[new_id] = new_substation
        # Re-map the labelled lines to the new substations
        for line_id, line in sub_dropped_lines.iterrows():
            for new_sub_id, sub in new_substations.iterrows():
                if line["interconnect"] == sub["NAME"].split("_")[1]:
                    if line["SUB_1_ID"] == sub_id:
                        lines.loc[line_id, "SUB_1_ID"] = new_sub_id
                    if line["SUB_2_ID"] == sub_id:
                        lines.loc[line_id, "SUB_2_ID"] = new_sub_id
    revised_g = nx.convert_matrix.from_pandas_edgelist(lines, "SUB_1_ID", "SUB_2_ID")
    sorted_interconnects = sorted(nx.connected_components(revised_g), key=len)[::-1]
    if len(sorted_interconnects) != len(interconnect_size_rank):
        interconnect_sizes = [len(c) for c in sorted_interconnects]
        raise ValueError(
            f"Interconnections were not separated successfully {interconnect_sizes}"
        )
    for i, name in enumerate(interconnect_size_rank):
        substations.loc[sorted_interconnects[i], "interconnect"] = name
    substations.drop(seams_substations, inplace=True)
