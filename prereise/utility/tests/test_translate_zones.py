import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Polygon

from prereise.utility.translate_zones import (
    filter_interesting_zones,
    format_zone_df,
    make_zones_valid,
    translate_zone_set,
)


def test_make_zones_valid():
    gdf = gpd.GeoDataFrame(
        {
            "geometry": [
                Polygon([(0, 3), (1, 3), (1, 2)]),  # valid
                Polygon([(0, 0), (1, 1), (1, 0), (0, 1)]),  # bowtie
                Polygon([(0, 1), (0.5, 0.5), (0, 0), (0, 1), (1, 0)]),  # flag
            ]
        },
        index=["a", "b", "c"],
    )
    gdf = make_zones_valid(gdf)

    assert gdf.is_valid.all()


def test_filter_interesting_zones():
    df = pd.DataFrame(
        {
            "a": [0, 0, 1, 0.5432],
            "b": [0.9, 1, 0, 0.5568],
            "c": [0, 0, 0, 0],
            "d": [0.1, 0, 0, 0],
        },
        index=["w", "x", "y", "z"],
    )
    assert filter_interesting_zones(df).to_dict() == {
        "a": {"w": "-", "z": 0.543},
        "b": {"w": 0.9, "z": 0.557},
        "d": {"w": 0.1, "z": "-"},
    }


def test_filter_interesting_zones_rounding():
    df = pd.DataFrame(
        {
            "a": [0, 0, 1, 0.5432],
            "b": [0.9, 1, 0, 0.5568],
            "c": [0, 0, 0, 0],
            "d": [0.1, 0, 0, 0],
        },
        index=["w", "x", "y", "z"],
    )
    assert filter_interesting_zones(df, rounding=1).to_dict() == {
        "a": {"w": "-", "z": 0.5},
        "b": {"w": 0.9, "z": 0.6},
        "d": {"w": 0.1, "z": "-"},
    }


def test_format_zone_df_happy_path():
    p = Polygon([(-34.58, -58.66), (-15.78, -47.91), (-33.45, -70.66)])
    mock_gdf = gpd.GeoDataFrame({"geometry": [p]}, crs="EPSG:4269")
    formatted_gdf = format_zone_df(mock_gdf, "foo")
    assert formatted_gdf.index == [0]
    assert list(formatted_gdf.columns) == ["foo", "geometry", "foo_area"]
    assert round(formatted_gdf.loc[0, "foo_area"]) == 3454055806157
    assert formatted_gdf.crs == "EPSG:3857"


def test_format_zone_df_invalid_geometry():
    invalid_bowtie = Polygon(
        [(-34.58, -58.66), (-15.78, -47.91), (-33.45, -70.66), (4.60, -74.08)]
    )
    mock_gdf = gpd.GeoDataFrame({"geometry": [invalid_bowtie]}, crs="EPSG:4269")
    with pytest.raises(ValueError):
        format_zone_df(mock_gdf, "foo")


def test_translate_zone_set_has_crs():
    with pytest.raises(ValueError):
        p = Polygon([(-34.58, -58.66), (-15.78, -47.91), (-33.45, -70.66)])
        mock_gdf_no_crs = gpd.GeoDataFrame({"geometry": [p]})
        translate_zone_set(mock_gdf_no_crs, mock_gdf_no_crs)


def test_translate_zone_set_happy_path():
    # zones_1 perfectly fit inside zones_2
    zones_1 = [
        Polygon([(-34.58, -58.66), (-15.78, -47.91), (-33.45, -70.66)]),
        Polygon([(-15.78, -47.91), (-33.45, -70.66), (4.60, -74.08)]),
    ]
    zones_2 = [
        Polygon([(-34.58, -58.66), (-15.78, -47.91), (4.60, -74.08), (-33.45, -70.66)])
    ]
    mock_gdf = gpd.GeoDataFrame(
        {"geometry": zones_1}, index=["a", "b"], crs="EPSG:4269"
    )
    mock_gdf_2 = gpd.GeoDataFrame({"geometry": zones_2}, index=["c"], crs="EPSG:4269")

    assert translate_zone_set(mock_gdf, mock_gdf_2).to_dict() == {
        "c": {"a": 1.0, "b": 1.0}
    }
    assert round(translate_zone_set(mock_gdf_2, mock_gdf), 3).to_dict() == {
        "a": {"c": 0.22},
        "b": {"c": 0.78},
    }


def test_translate_zone_set_self_overlap():
    zones_1 = [
        Polygon([(-34.58, -58.66), (-15.78, -47.91), (-33.45, -70.66)]),
        Polygon([(-15.78, -47.91), (-20, -51), (-33.45, -70.66), (4.60, -74.08)]),
    ]
    zones_2 = [
        Polygon([(-34.58, -58.66), (-15.78, -47.91), (4.60, -74.08), (-33.45, -70.66)])
    ]
    mock_gdf = gpd.GeoDataFrame(
        {"geometry": zones_1}, index=["a", "b"], crs="EPSG:4269"
    )
    mock_gdf_2 = gpd.GeoDataFrame({"geometry": zones_2}, index=["c"], crs="EPSG:4269")

    assert translate_zone_set(mock_gdf, mock_gdf_2).to_dict() == {
        "c": {"a": 1.0, "b": 1.0}
    }
    assert round(translate_zone_set(mock_gdf_2, mock_gdf), 3).to_dict() == {
        "a": {"c": 0.211},
        "b": {"c": 0.789},
    }


def test_translate_zone_set_gap():
    zones_1 = [
        Polygon([(-34.58, -58.66), (-15.78, -47.91), (-33.45, -70.66)]),
        Polygon([(-15.78, -47.91), (-16, -55), (-33.45, -70.66), (4.60, -74.08)]),
    ]
    zones_2 = [
        Polygon([(-34.58, -58.66), (-15.78, -47.91), (4.60, -74.08), (-33.45, -70.66)])
    ]
    mock_gdf = gpd.GeoDataFrame(
        {"geometry": zones_1}, index=["a", "b"], crs="EPSG:4269"
    )
    mock_gdf_2 = gpd.GeoDataFrame({"geometry": zones_2}, index=["c"], crs="EPSG:4269")

    assert translate_zone_set(mock_gdf, mock_gdf_2).to_dict() == {
        "c": {"a": 1.0, "b": 1.0}
    }
    assert round(translate_zone_set(mock_gdf_2, mock_gdf), 3).to_dict() == {
        "a": {"c": 0.238},
        "b": {"c": 0.762},
    }


def test_translate_zone_set_isolated():
    zones_1 = [
        Polygon([(-34.58, -58.66), (-15.78, -47.91), (-33.45, -70.66)]),
        Polygon([(-15.78, -47.91), (-33.45, -70.66), (4.60, -74.08)]),
        Polygon([(0, -55), (5, -50), (5, -55)]),  # isolated zone
    ]
    zones_2 = [
        Polygon([(-34.58, -58.66), (-15.78, -47.91), (4.60, -74.08), (-33.45, -70.66)])
    ]
    mock_gdf = gpd.GeoDataFrame(
        {"geometry": zones_1}, index=["a", "b", "c"], crs="EPSG:4269"
    )
    mock_gdf_2 = gpd.GeoDataFrame({"geometry": zones_2}, index=["d"], crs="EPSG:4269")

    mock_gdf.plot(color="green", alpha=0.5)

    assert translate_zone_set(mock_gdf, mock_gdf_2).to_dict() == {
        "d": {"a": 1.0, "b": 1.0, "c": 0.0}
    }
    assert round(translate_zone_set(mock_gdf_2, mock_gdf), 3).to_dict() == {
        "a": {"d": 0.22},
        "b": {"d": 0.78},
        "c": {"d": 0},
    }
