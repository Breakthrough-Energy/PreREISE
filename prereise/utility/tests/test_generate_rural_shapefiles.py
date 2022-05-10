import json

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

    # Convert to json then back to dict -- this unpacks the Polygon objects
    assert json.loads(r_and_u.to_json()) == {
        "type": "FeatureCollection",
        "features": [
            {
                "id": "0",
                "type": "Feature",
                "properties": {"state": "CO", "urban": True},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [[0.1, 0.1], [0.1, 0.5], [0.5, 0.5], [0.5, 0.1], [0.1, 0.1]]
                    ],
                },
            },
            {
                "id": "1",
                "type": "Feature",
                "properties": {"state": "CO", "urban": True},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [[4.0, 4.0], [4.0, 4.5], [4.5, 4.5], [4.5, 4.0], [4.0, 4.0]]
                    ],
                },
            },
            {
                "id": "2",
                "type": "Feature",
                "properties": {"state": "CO", "urban": False},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [[5.0, 5.0], [5.0, 0.0], [0.0, 0.0], [0.0, 5.0], [5.0, 5.0]],
                        [[4.5, 4.0], [4.5, 4.5], [4.0, 4.5], [4.0, 4.0], [4.5, 4.0]],
                        [[0.5, 0.5], [0.1, 0.5], [0.1, 0.1], [0.5, 0.1], [0.5, 0.5]],
                    ],
                },
            },
        ],
    }
