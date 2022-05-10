import os

import geopandas as gpd

from prereise.gather.const import abv2state
from prereise.utility.shapefile import download_shapefiles


def append_rural_areas_to_urban(states, urban_areas):
    """Takes shapefiles of US States and US urban areas, filters to the
    contiguous 48 states, and adds rural areas (areas that are not urban) to
    the geodataframe.

    :param geopandas.geodataframe.GeoDataFrame states: US state outlines
    :param geopandas.geodataframe.GeoDataFrame urban_areas: US urban area outlines
    :return: (*geopandas.geodataframe.GeoDataFrame*) -- new gdf of urban and rural areas
        includes a column indicating whether the area is urban or not
    """
    lower_48_states_abv = list(abv2state.keys())
    lower_48_states_abv.remove("AK")
    lower_48_states_abv.remove("HI")

    states = states.rename(columns={"STUSPS": "state"})
    states = states.loc[states["state"].isin(lower_48_states_abv)]

    urban_areas["state"] = urban_areas["NAME10"].str[-2:]
    # this drops 66 out of 3601 rows
    urban_areas = urban_areas.loc[urban_areas["state"].isin(lower_48_states_abv)]
    urban_areas["urban"] = True

    rural_areas = states.overlay(urban_areas, how="difference")
    rural_areas["urban"] = False

    return urban_areas.append(rural_areas, ignore_index=True)[
        ["state", "geometry", "urban"]
    ]


def generate_urban_and_rural_shapefiles():
    """Downloads shapefiles of state outlines and urban areas from BES azure blob storage.
    Writes these shapefiles to a local folder, then creates new shapefiles that
    include both urban and rural areas.

    :return: (*str*) -- path to the new shapefiles
    """
    base_url = "https://besciences.blob.core.windows.net/shapefiles/USA/"

    states_folder = os.path.join(os.path.dirname(__file__), "state-outlines")
    states_file = download_shapefiles(
        f"{base_url}state-outlines/",
        "cb_2018_us_state_20m",
        states_folder,
    )
    states = gpd.read_file(states_file)

    urban_folder = os.path.join(os.path.dirname(__file__), "urban-areas")
    urban_file = download_shapefiles(
        f"{base_url}urban-areas/",
        "cb_2019_us_ua10_500k",
        urban_folder,
    )
    urban_areas = gpd.read_file(urban_file)

    urban_and_rural_areas = append_rural_areas_to_urban(states, urban_areas)

    os.makedirs("./urban-and-rural-areas", exist_ok=True)
    filepath = "./urban-and-rural-areas/urban-and-rural-areas.shp"
    urban_and_rural_areas.to_file(filepath)
    return filepath
