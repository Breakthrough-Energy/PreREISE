import geopandas as gpd
import pandas as pd
from powersimdata.input.grid import Grid
from shapely.geometry import Point, Polygon

from prereise.utility.translate_urban_rural_to_usa_tamu import (
    create_substation_gdf,
    create_usa_tamu_convex_hull_shapefile,
    fix_lz_border,
    format_states_gdf,
)

WA_lz_polygon = Polygon([(1, 1), (0, 5), (5, 6), (4, 1)])
CA_lz_polygon = Polygon([(0, 10), (0, 15), (5, 15), (5, 10)])
WA_border_polygon = Polygon([(0, 0), (0, 5), (5, 5), (5, 0)])
CA_border_polygon = Polygon([(0, 10), (0, 20), (3, 20), (3, 10)])
HI_border_polygon = Polygon([(100, 100), (100, 105), (105, 105)])

# Mock US State borders
states = gpd.GeoDataFrame(
    {
        "geometry": [WA_border_polygon, CA_border_polygon, HI_border_polygon],
        "STUSPS": ["WA", "CA", "HI"],
    }
)
formatted_states = gpd.GeoDataFrame(
    {
        "geometry": {"WA": WA_border_polygon, "CA": CA_border_polygon},
        "state": {"WA": "WA", "CA": "CA"},
    }
)
sub_gdf = gpd.GeoDataFrame(
    {
        "zone": {122: "Bay Area", 6134: "Washington"},
        "geometry": {122: Point(2, 3), 6134: Point(14, 4)},
    }
)


def test_format_states_gdf():
    results = format_states_gdf(states)
    assert formatted_states.to_dict() == results.to_dict()


class MockGrid:
    def __init__(self):
        """Constructor"""
        self.bus2sub = pd.DataFrame({"sub_id": {0: 122, 1: 122, 2: 6134}})
        self.bus = pd.DataFrame({"zone_id": {0: 204, 1: 204, 2: 201}})
        self.id2zone = {204: "Bay Area", 201: "Washington"}
        self.sub = pd.DataFrame({"lon": {122: 2, 6134: 14}, "lat": {122: 3, 6134: 4}})

    @property
    def __class__(self):
        """If anyone asks, I'm a Grid object!"""
        return Grid


def test_create_substation_gdf():
    mock_grid = MockGrid()
    results = create_substation_gdf(mock_grid)
    assert sub_gdf.to_dict() == results.to_dict()


def test_fix_lz_border_single_lz():
    results = fix_lz_border(formatted_states, "WA", WA_lz_polygon)
    expected = WA_border_polygon
    assert expected == results


def test_fix_lz_border_multi_lz():
    results = fix_lz_border(formatted_states, "CA", CA_lz_polygon)
    expected = Polygon([(0, 15), (3, 15), (3, 10), (0, 10)])
    assert expected == results


def test_create_usa_tamu_convex_hull_shapefile():
    # gdf where CA substations match CA_lz_polygon
    sub_gdf_2 = gpd.GeoDataFrame(
        {
            "zone": {
                122: "Bay Area",
                123: "Bay Area",
                124: "Bay Area",
                125: "Bay Area",
                6134: "Washington",
            },
            "geometry": {
                122: Point(0, 10),
                123: Point(0, 15),
                124: Point(5, 15),
                125: Point(5, 10),
                6134: Point(14, 4),
            },
        }
    )
    results = create_usa_tamu_convex_hull_shapefile(sub_gdf_2, formatted_states)
    expected = {
        "geometry": {
            "Bay Area": Polygon([(0, 15), (3, 15), (3, 10), (0, 10)]),
            "Washington": WA_border_polygon,
        },
        "state": {"Bay Area": "CA", "Washington": "WA"},
    }
    assert expected == results.to_dict()
