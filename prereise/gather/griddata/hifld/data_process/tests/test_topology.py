import pandas as pd
from powersimdata.utility.distance import haversine

from prereise.gather.griddata.hifld.data_process.topology import (
    connect_islands_with_minimum_cost,
    find_adj_state_of_2_conn_comp,
    min_dist_of_2_conn_comp,
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
    assert connect_islands_with_minimum_cost(lines, subs) == expected_return
