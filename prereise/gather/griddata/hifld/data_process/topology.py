from itertools import product


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
