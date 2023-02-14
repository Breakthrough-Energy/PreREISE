import io
import os
import zipfile

import geopandas as gpd
import pandas as pd
import requests


def read_shapefile(url):
    """Read shape files for overlay

    :param str url: directory in blob storage that contain the shape file in zip format
    :return: (*geopandas.GeoDataFrame*) -- geo data frame of the shape file
    """
    local_path = "tmp/"
    r = requests.get(url)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(path=local_path)  # extract to folder
    filenames = [
        y for y in sorted(z.namelist()) if y[-3:] in {"dbf", "prj", "shp", "shx"}
    ]
    dbf, prj, shp, shx = [filename for filename in filenames]

    shapefile_df = gpd.GeoDataFrame(gpd.read_file((local_path + shp))).to_crs(
        "EPSG:4269"
    )

    return shapefile_df


def zone_shp_overlay(zone_name_shp, zone_shp, pumas_shp):
    """Select pumas within a zonal load area

    :param str zone_name_shp: name of the zone in ba_area.shp
    :param geopandas.GeoDataFrame zone_shp: geo data frame of zone(BA) shape file
    :param geopandas.GeoDataFrame pumas_shp: geo data frame of pumas shape file
    :return: (*pandas.DataFrame*) -- puma data of all pumas within the zone,
        including fraction within the zone
    """
    zone_shp = zone_shp[zone_shp["BA"] == zone_name_shp].copy()
    pumas_shp["area"] = pumas_shp["geometry"].to_crs({"proj": "cea"}).area
    puma_zone = gpd.overlay(pumas_shp, zone_shp.to_crs("EPSG:4269"))
    puma_zone["area"] = puma_zone["geometry"].to_crs({"proj": "cea"}).area
    puma_zone["puma"] = "puma_" + puma_zone["GEOID10"]

    puma_zone["area_frac"] = [
        puma_zone["area"][i]
        / list(pumas_shp[pumas_shp["puma"] == puma_zone["puma"][i]]["area"])[0]
        for i in range(len(puma_zone))
    ]

    puma_data_zone = pd.DataFrame(
        {"puma": puma_zone["puma"], "frac_in_zone": puma_zone["area_frac"]}
    )

    puma_data = pd.read_csv(
        os.path.join(os.path.dirname(__file__), "data", "puma_data.csv"),
        index_col="puma",
    )
    puma_hp = pd.read_csv(
        os.path.join(os.path.dirname(__file__), "data", "puma_hp_data.csv"),
        index_col="puma",
    )
    puma_data_zone = puma_data_zone.join(puma_data, on="puma")
    puma_data_zone = puma_data_zone.join(puma_hp.drop(columns=["state"]), on="puma")
    puma_data_zone = puma_data_zone.set_index("puma")

    return puma_data_zone


def state_shp_overlay(state, state_shp, zone_shp):
    """Select load zones within a state

    :param str state: abbrev. of state
    :param geopandas.GeoDataFrame state_shp: geo data frame of state shape file
    :param geopandas.GeoDataFrame zone_shp: geo data frame of zone(BA) shape file
    :return: (*geopandas.GeoDataFrame*) -- state boundaries and load zones within it
    """
    if state == "United States":
        state_shape = state_shp[state_shp["NAME"] == state].copy()
    else:
        state_shape = state_shp[state_shp["STUSPS"] == state].copy()

    zone_shp["area"] = zone_shp["geometry"].to_crs({"proj": "cea"}).area

    zone_state = gpd.overlay(zone_shp, state_shape.to_crs("EPSG:4269"))
    zone_state["area"] = zone_state["geometry"].to_crs({"proj": "cea"}).area
    zone_state["area_frac"] = [
        zone_state["area"][i]
        / list(zone_shp[zone_shp["BA"] == zone_state["BA"][i]]["area"])[0]
        for i in range(len(zone_state))
    ]
    zone_state.loc[zone_state["area_frac"] >= 0.99, "area_frac"] = 1
    zone_state = zone_state.drop(zone_state[zone_state["area_frac"] <= 0.00001].index)

    return zone_state
