import numpy as np
import pandas as pd
import pytest
from powersimdata.utility.distance import haversine, ll2uv

from prereise.gather.griddata.hifld.data_process.topology import (
    connect_islands_with_minimum_cost,
    find_adj_state_of_2_conn_comp,
    identify_bottlenecks,
    min_dist_of_2_conn_comp,
    min_dist_of_2_conn_comp_kdtree,
)

cc1 = pd.DataFrame(
    {
        "STATE": ["WA", "WA"],
        "LATITUDE": [48.188346, 48.214966],
        "LONGITUDE": [-122.113003, -122.028332],
    },
    index=[200352, 209798],
)

cc2 = pd.DataFrame(
    {
        "STATE": ["WA", "WA"],
        "LATITUDE": [47.838214, 47.837820],
        "LONGITUDE": [-117.410093, -117.352394],
    },
    index=[209809, 200594],
)

cc3 = pd.DataFrame(
    {
        "STATE": ["OR", "OR"],
        "LATITUDE": [44.071550, 44.071263],
        "LONGITUDE": [-122.966880, -122.972234],
    },
    index=[202058, 202059],
)

subs = pd.concat([cc1, cc2, cc3])
lines = pd.DataFrame(
    {
        "SUB_1_ID": [cc1.index[0], cc2.index[0], cc3.index[0]],
        "SUB_2_ID": [cc1.index[1], cc2.index[1], cc3.index[1]],
    }
)


def test_min_dist_of_2_conn_comp():
    inputs = [cc1[["LATITUDE", "LONGITUDE"]], cc2[["LATITUDE", "LONGITUDE"]], haversine]
    d, r1, r2 = min_dist_of_2_conn_comp(*inputs)
    expected_return = [
        haversine((48.214966, -122.0283320), (47.838214, -117.410093)),
        209798,
        209809,
    ]
    assert [d, r1, r2] == expected_return


def test_min_dist_of_2_conn_comp_kdtree():
    inputs = [cc1[["LATITUDE", "LONGITUDE"]], cc2[["LATITUDE", "LONGITUDE"]]]
    d, r1, r2 = min_dist_of_2_conn_comp_kdtree(*inputs, p=1)
    expected_return = [
        sum(
            [
                abs(e1 - e2)
                for e1, e2 in zip(
                    ll2uv(-122.0283320, 48.214966), ll2uv(-117.410093, 47.838214)
                )
            ]
        ),
        209798,
        209809,
    ]
    assert [d, r1, r2] == expected_return


def test_min_dist_of_2_conn_comp_kdtree_swap():
    inputs = [cc2[["LATITUDE", "LONGITUDE"]].head(1), cc1[["LATITUDE", "LONGITUDE"]]]
    d, r1, r2 = min_dist_of_2_conn_comp_kdtree(*inputs, p=1)
    expected_return = [
        sum(
            [
                abs(e1 - e2)
                for e1, e2 in zip(
                    ll2uv(-122.0283320, 48.214966), ll2uv(-117.410093, 47.838214)
                )
            ]
        ),
        209809,
        209798,
    ]
    assert [d, r1, r2] == expected_return


def test_find_adj_state_of_2_conn_comp():
    inputs = [
        (cc1.index, cc2.index, {"WA": []}, subs),
        (cc2.index, cc3.index, {"WA": ["OR"], "OR": ["WA"]}, subs),
    ]
    expected_return = [({"WA"}, {"WA"}), ({"WA"}, {"OR"})]
    for i, e in zip(inputs, expected_return):
        assert find_adj_state_of_2_conn_comp(*i) == e


def test_connect_islands_with_minimum_cost():
    expected_return = (
        [
            (
                0,
                1,
                {
                    "weight": haversine(
                        subs.loc[209798, ["LATITUDE", "LONGITUDE"]],
                        subs.loc[209809, ["LATITUDE", "LONGITUDE"]],
                    ),
                    "start": 209798,
                    "end": 209809,
                },
            ),
            (
                0,
                2,
                {
                    "weight": haversine(
                        subs.loc[200352, ["LATITUDE", "LONGITUDE"]],
                        subs.loc[202058, ["LATITUDE", "LONGITUDE"]],
                    ),
                    "start": 200352,
                    "end": 202058,
                },
            ),
            (
                1,
                2,
                {
                    "weight": haversine(
                        subs.loc[209809, ["LATITUDE", "LONGITUDE"]],
                        subs.loc[202058, ["LATITUDE", "LONGITUDE"]],
                    ),
                    "start": 209809,
                    "end": 202058,
                },
            ),
        ],
        [
            (
                0,
                1,
                {
                    "weight": haversine(
                        subs.loc[209798, ["LATITUDE", "LONGITUDE"]],
                        subs.loc[209809, ["LATITUDE", "LONGITUDE"]],
                    ),
                    "start": 209798,
                    "end": 209809,
                },
            ),
            (
                0,
                2,
                {
                    "weight": haversine(
                        subs.loc[200352, ["LATITUDE", "LONGITUDE"]],
                        subs.loc[202058, ["LATITUDE", "LONGITUDE"]],
                    ),
                    "start": 200352,
                    "end": 202058,
                },
            ),
        ],
    )
    expected_return_kdtree = (
        [
            (
                0,
                1,
                {
                    "start": 209798,
                    "end": 209809,
                },
            ),
            (
                0,
                2,
                {
                    "start": 200352,
                    "end": 202058,
                },
            ),
            (
                1,
                2,
                {
                    "start": 209809,
                    "end": 202058,
                },
            ),
        ],
        [
            (
                0,
                1,
                {
                    "start": 209798,
                    "end": 209809,
                },
            ),
            (
                0,
                2,
                {
                    "start": 200352,
                    "end": 202058,
                },
            ),
        ],
    )
    assert connect_islands_with_minimum_cost(lines, subs) == expected_return
    assert (
        connect_islands_with_minimum_cost(lines, subs, memory_efficient=True)
        == expected_return
    )
    all_edges, mst_edges = connect_islands_with_minimum_cost(
        lines, subs, min_dist_method="kdtree"
    )
    for e in all_edges + mst_edges:
        e[2].pop("weight")
    assert (all_edges, mst_edges) == expected_return_kdtree


def test_identify_bottlenecks():
    branch = pd.DataFrame(
        [
            {"from_bus_id": 1, "to_bus_id": 2},
            {"from_bus_id": 2, "to_bus_id": 3},
            {"from_bus_id": 2, "to_bus_id": 4},
            {"from_bus_id": 2, "to_bus_id": 5},
            {"from_bus_id": 2, "to_bus_id": 6},
            {"from_bus_id": 3, "to_bus_id": 4},
            {"from_bus_id": 5, "to_bus_id": 6},
            {"from_bus_id": 5, "to_bus_id": 7},
            {"from_bus_id": 6, "to_bus_id": 7},
            {"from_bus_id": 7, "to_bus_id": 8},
            {"from_bus_id": 7, "to_bus_id": 11},
            {"from_bus_id": 8, "to_bus_id": 9},
            {"from_bus_id": 8, "to_bus_id": 11},
            {"from_bus_id": 8, "to_bus_id": 12},
            {"from_bus_id": 8, "to_bus_id": 14},
            {"from_bus_id": 8, "to_bus_id": 15},
            {"from_bus_id": 15, "to_bus_id": 8},  # Same nodes, different orientation
            {"from_bus_id": 9, "to_bus_id": 10},
            {"from_bus_id": 9, "to_bus_id": 11},
            {"from_bus_id": 10, "to_bus_id": 11},
            {"from_bus_id": 10, "to_bus_id": 16},
            {"from_bus_id": 10, "to_bus_id": 17},
            {"from_bus_id": 10, "to_bus_id": 18},
            {"from_bus_id": 12, "to_bus_id": 13},
            {"from_bus_id": 13, "to_bus_id": 14},
            {"from_bus_id": 13, "to_bus_id": 15},
            {"from_bus_id": 17, "to_bus_id": 18},
        ]
    )
    branch["capacity"] = branch["from_bus_id"] * branch["to_bus_id"] / 50
    demand = pd.Series(np.arange(0.1, 1.9, 0.1), index=range(1, 19))
    bottlenecks = identify_bottlenecks(
        branch, demand, root=frozenset({7, 8, 9, 10, 11})
    )
    expected_all_keys = {
        (8, frozenset({8, 12, 13, 14, 15})),
        (frozenset({7, 8, 9, 10, 11}), 8),
        (10, frozenset({10, 16})),
        (10, frozenset({10, 17, 18})),
        (frozenset({7, 8, 9, 10, 11}), 10),
        (2, frozenset({2, 3, 4})),
        (2, frozenset({1, 2})),
        (frozenset({2, 5, 6, 7}), 2),
        (7, frozenset({2, 5, 6, 7})),
        (frozenset({7, 8, 9, 10, 11}), 7),
    }
    expected_constrained_keys = {
        (frozenset({7, 8, 9, 10, 11}), 8),
        (frozenset({7, 8, 9, 10, 11}), 10),
        (2, frozenset({2, 3, 4})),
        (2, frozenset({1, 2})),
        (frozenset({2, 5, 6, 7}), 2),
        (7, frozenset({2, 5, 6, 7})),
        (frozenset({7, 8, 9, 10, 11}), 7),
    }
    assert set(bottlenecks["all"]) == expected_all_keys
    assert set(bottlenecks["constrained"]) == expected_constrained_keys
    for k, v in bottlenecks["all"].items():
        assert set(v.keys()) == {"capacity", "demand", "descendants"}
        assert isinstance(v["capacity"], float)
        assert isinstance(v["demand"], float)
        assert isinstance(v["descendants"], set)
    for k, v in bottlenecks["constrained"].items():
        assert v == bottlenecks["all"][k]
    results_to_check = {
        (8, frozenset({8, 12, 13, 14, 15})): {
            "descendants": set(),
            "demand": 5.4,
            "capacity": 8.96,
        },
        (2, frozenset({2, 3, 4})): {
            "descendants": set(),
            "demand": 0.7,
            "capacity": 0.28,
        },
        (frozenset({2, 5, 6, 7}), 2): {
            "descendants": {1, 3, 4},
            "demand": 1.0,
            "capacity": 0.44,
        },
        (7, frozenset({2, 5, 6, 7})): {
            "descendants": {1, 2, 3, 4},
            "demand": 2.1,
            "capacity": 1.54,
        },
        (frozenset({7, 8, 9, 10, 11}), 7): {
            "descendants": {1, 2, 3, 4, 5, 6},
            "demand": 2.8,
            "capacity": 2.66,
        },
    }
    for key, result in results_to_check.items():
        for subkey, subresult in result.items():
            assert bottlenecks["all"][key][subkey] == pytest.approx(result[subkey])
