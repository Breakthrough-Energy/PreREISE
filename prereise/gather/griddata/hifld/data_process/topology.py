from itertools import combinations, product

import networkx as nx
from powersimdata.utility.distance import haversine
from tqdm import tqdm

from prereise.gather.griddata.hifld.const import abv_state_neighbor


def min_dist_of_2_conn_comp(nodes1, nodes2, dist_metric):
    """Calculate the minimum distance of two connected components based on the given
    distance metric.

    :param pandas.DataFrame nodes1: a data frame contains all the nodes of the first
        connected component with index being node ID and two columns being latitude
        and longitude in order.
    :param pandas.DataFrame nodes2: a data frame contains all the nodes of the second
        connected component with index being node ID and two columns being latitude
        and longitude in order.
    :param func dist_metric: a function defines the distance metric.
    :return: (*tuple*) -- a tuple contains three elements, the minimum distance
        follows by a pair of nodes from the two connected components respectively
        in order
    """
    min_dist = float("inf")
    for v1, v2 in product(nodes1.index, nodes2.index):
        tmp_dist = dist_metric(nodes1.loc[v1], nodes2.loc[v2])
        if tmp_dist < min_dist:
            min_dist, res_v1, res_v2 = tmp_dist, v1, v2
    return min_dist, res_v1, res_v2


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
    lines, subs, cost_metric=haversine, state_neighbor=None
):
    """Connect a group of islands defined by lines and substations into one big
    island with minimum cost.

    :param pandas.DataFrame lines: line data frame indexed by ``ID`` with two columns
        ``SUB_1_ID`` and ``SUB_2_ID`` representing the corresponding substations at the
        start and end points.
    :param pandas.DataFrame subs: substation data frame indexed by ``ID`` with two
        columns ``LATITUDE`` and ``LONGITUDE`` representing the geographical
        coordination of each entry.
    :param function cost_metric: a function defines the cost metric to calculate the
        weight of lines, defaults to :py:func:`haversine`.
    :param dict state_neighbor: a dictionary defines the adjacency relationship among
        states, defaults to None and the constant dictionary ``abv_state_neighbor``
        defined in the ``const`` module is used.
    :return: (*tuple*) -- a pair of lists, the first one is a list of all potential
        line candidates among given connected components; the second one is a list
        of subsequence of the first entry, representing the chosen lines to form a
        minimum spanning tree. Each entry of both lists is a 3-tuple, index of the
        first connected component, index of the second connected component,
        a dictionary with keys containing ``start``, ``end`` and ``weight``, defines
        the ``from substation ID``, ``to substation ID`` and the weight of the line
        calculated by the ``cost_metric``.

        .. note:: the indexes of connected components are defined by the size,
            i.e. number of nodes, of the connected components in ascending order.
    """
    if state_neighbor is None:
        state_neighbor = abv_state_neighbor

    # Construct a networkx graph using lines data frame
    graph = nx.convert_matrix.from_pandas_edgelist(lines, "SUB_1_ID", "SUB_2_ID")

    # Get the full list of connected components of the resultant graph sored by size in
    # ascending order
    all_cc = sorted(list(nx.connected_components(graph)), key=len)

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
            min_dist, sub1, sub2 = min_dist_of_2_conn_comp(nodes1, nodes2, cost_metric)
            edge_list.append(
                (ind1, ind2, {"weight": min_dist, "start": sub1, "end": sub2})
            )
    # Build a minimum spanning tree based on the weighted edge list
    cc_graph = nx.Graph()
    cc_graph.add_edges_from(edge_list)
    cc_mst = nx.minimum_spanning_tree(cc_graph)
    return edge_list, sorted(cc_mst.edges(data=True))
