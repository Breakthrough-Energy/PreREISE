import geopandas as gpd
from shapely.geometry import Polygon

from prereise.utility.generate_rural_shapefiles import append_rural_areas_to_urban


def test_append_rural_areas_to_urban():
    mock_states = gpd.GeoDataFrame(
        {
            "geometry": [
                Polygon([(0, 0), (0, 5), (5, 5), (5, 0)]),
            ],
            "STUSPS": ["CO"],
        }
    )
    mock_urban = gpd.GeoDataFrame(
        {
            "geometry": [
                Polygon([(0.1, 0.1), (0.1, 0.5), (0.5, 0.5), (0.5, 0.1)]),
                Polygon([(4, 4), (4, 4.5), (4.5, 4.5), (4.5, 4)]),
                Polygon([(10, 10), (10, 13), (13, 13), (13, 10)]),
            ],
            "NAME10": ["Denver_CO", "Boulder_CO", "Honolulu_HI"],
        }
    )

    r_and_u = append_rural_areas_to_urban(mock_states, mock_urban)

    expected = {
        "geometry": {
            "Boulder_CO": Polygon(
                [[4.0, 4.0], [4.0, 4.5], [4.5, 4.5], [4.5, 4.0], [4.0, 4.0]]
            ),
            "CO_rural": Polygon(
                [[5.0, 5.0], [5.0, 0.0], [0.0, 0.0], [0.0, 5.0], [5.0, 5.0]],
                [
                    [[4.5, 4.0], [4.5, 4.5], [4.0, 4.5], [4.0, 4.0], [4.5, 4.0]],
                    [[0.5, 0.5], [0.1, 0.5], [0.1, 0.1], [0.5, 0.1], [0.5, 0.5]],
                ],
            ),
            "Denver_CO": Polygon(
                [[0.1, 0.1], [0.1, 0.5], [0.5, 0.5], [0.5, 0.1], [0.1, 0.1]]
            ),
        },
        "state": {"Boulder_CO": "CO", "CO_rural": "CO", "Denver_CO": "CO"},
        "urban": {"Boulder_CO": True, "CO_rural": False, "Denver_CO": True},
    }

    assert r_and_u.to_dict() == expected
