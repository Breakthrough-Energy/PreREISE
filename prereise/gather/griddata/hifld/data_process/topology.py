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
    """Find the adjacency states between two given connected components.

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
    cc1_neighbors = cc1_all_state.copy()
    cc2_neighbors = cc2_all_state.copy()
    for s in cc1_all_state:
        cc1_neighbors |= set(state_adj[s])
    for s in cc2_all_state:
        cc2_neighbors |= set(state_adj[s])
    cc1_adj = cc2_neighbors & cc1_all_state
    cc2_adj = cc1_neighbors & cc2_all_state
    return cc1_adj, cc2_adj
