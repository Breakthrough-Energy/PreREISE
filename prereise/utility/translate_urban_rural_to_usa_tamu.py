import os

import geopandas as gpd
from powersimdata.input.grid import Grid

from prereise.gather.const import lower_48_states_abv, zone2state_abv
from prereise.utility.shapefile import download_shapefiles
from prereise.utility.translate_zones import translate_zone_set

seen = set()
states_with_multiple_loadzones = set(
    [
        state
        for state in list(zone2state_abv.values())
        if state in seen or seen.add(state)
    ]
)


def plot_loadzones(tamu_loadzones, substations, states):
    """Plot usa tamu loadzone borders and substations as choropleth.
       Has 20 colors; buckets zones in alphabetical order.

    :param geopandas.geodataframe.GeoDataFrame tamu_loadzones: GeoDataFrame with
        index = zone, columns = ['geometry']
    :param geopandas.geodataframe.GeoDataFrame substations: GeoDataFrame with
        index = substation id, columns = ['geometry', 'zone']
    :param geopandas.geodataframe.GeoDataFrame states: GeoDataFrame of lower 48
        US state borders with index = state, columns = ['geometry']
    :return: (*matplotlib.axes._subplots.AxesSubplot*) -- the plot object
    """
    ax = tamu_loadzones.plot(figsize=(50, 50), cmap="tab20", alpha=0.5)
    substations.plot(
        ax=ax,
        column="zone",
        linewidth=1,
        cmap="tab20",
    )
    tamu_loadzones.plot(ax=ax, linewidth=1, edgecolor="red", color="none", alpha=0.5)
    states.plot(
        ax=ax,
        linewidth=1,
        edgecolor="black",
        color="none",
    )
    return ax


def format_states_gdf(states):
    """Takes geodataframe of US state borders, filters to the lower 48 states,
       and renames columns.

    :param geopandas.geodataframe.GeoDataFrame states: GeoDataFrame of US state
        borders with index = state, columns = ['geometry', 'STUSPS']
    :return: (*geopandas.geodataframe.GeoDataFrame*) -- modified states gdf
    """
    states = states.rename(columns={"STUSPS": "state"})
    states = states.loc[states["state"].isin(lower_48_states_abv)]
    states.index = states["state"]
    return states


def create_substation_gdf(grid):
    """Takes a grid object and uses lat lon data to create a Geodataframe of
       substations.

    :param powersimdata.input.grid.Grid grid: Grid instance.
    :return: (*geopandas.geodataframe.GeoDataFrame*) -- gdf of substations
    """
    sub2zone = grid.bus2sub.copy().join(grid.bus["zone_id"])[["sub_id", "zone_id"]]
    sub2zone = sub2zone.groupby(["sub_id", "zone_id"]).sum()
    sub2zone = sub2zone.reset_index(level="zone_id")

    sub = grid.sub.join(sub2zone)
    sub["zone"] = sub["zone_id"].replace(grid.id2zone)

    sub = gpd.GeoDataFrame(sub, geometry=gpd.points_from_xy(sub.lon, sub.lat))
    sub = sub[["zone", "geometry"]]

    return sub


def fix_lz_border(states, state, geometry):
    """Takes a shape representing a loadzone and trims it to match state
       borders. If there is only one loadzone in that state, we use the
       original state border. If there are multiple loadzones in one state, we
       trim the loadzone borders so they do not go outside the state border.

    :param geopandas.geodataframe.GeoDataFrame states: GeoDataFrame of lower 48
        US state borders with index = state, columns = ['geometry', 'state']
    :param str state: Abbreviated name of the state.
    :param TODO geometry: The shape of the loadzone to be trimmed
    :return: (*TODO*) -- the modified loadzone shape
    """

    state_geom = states.loc[state, "geometry"]

    if state in states_with_multiple_loadzones:
        # Make sure loadzones don't go outside state borders
        return geometry.intersection(state_geom)
    else:
        # Replace single loadzone states with state border shape
        return state_geom


def create_usa_tamu_convex_hull_shapefile(sub_gdf, states):
    """Creates a Geodataframe that approximates the shapes of the USA tamu
       loadzones. Loadzone shapes are made by taking the convex hull of all the
       individual substations within that zone. A convex hull is the smallest
       convex polygon containing all the points in each geometry.

    :param geopandas.geodataframe.GeoDataFrame sub_gdf: GeoDataFrame of
        substations with index = sub id, columns = ['geometry', 'zone']
    :param geopandas.geodataframe.GeoDataFrame states: GeoDataFrame of lower 48
        US state borders with index = state, columns = ['geometry', 'state']
    :return: (*geopandas.geodataframe.GeoDataFrame*) -- gdf of USA tamu zones
    """

    tamu_loadzones = sub_gdf.dissolve("zone").convex_hull
    tamu_loadzones = gpd.GeoDataFrame(tamu_loadzones)
    tamu_loadzones = tamu_loadzones.rename(columns={0: "geometry"})

    tamu_loadzones["state"] = tamu_loadzones.index
    tamu_loadzones["state"] = tamu_loadzones["state"].replace(zone2state_abv)

    # epsg:4269 matches urban_rural and is most commonly used by U.S. federal agencies.
    # https://www.nceas.ucsb.edu/sites/default/files/2020-04/OverviewCoordinateReferenceSystems.pdf
    tamu_loadzones = tamu_loadzones.set_crs("epsg:4269")

    tamu_loadzones["geometry"] = tamu_loadzones.apply(
        lambda x: fix_lz_border(states, x.state, x.geometry),
        axis=1,
    )

    return tamu_loadzones


def translate_urban_rural_to_usa_tamu():
    """Downloads US state borders as well as census data for urban and rural
       areas in the US. Creates a matrix that can be used to transform

    :return: (*pandas.DataFrame*) -- matrix of urban and rural zones to USA tamu zones
    """
    base_url = "https://besciences.blob.core.windows.net/shapefiles/USA/"

    # download states shapefiles
    states_folder = os.path.join(os.path.dirname(__file__), "state-outlines")
    states_file = download_shapefiles(
        f"{base_url}state-outlines/",
        "cb_2018_us_state_20m",
        states_folder,
    )
    states = gpd.read_file(states_file)
    states = format_states_gdf(states)

    # download urban-and-rural shapefiles
    urban_and_rural_folder = os.path.join(
        os.path.dirname(__file__), "urban-and-rural-areas"
    )
    urban_and_rural_file = download_shapefiles(
        f"{base_url}urban-and-rural-areas/",
        "urban-and-rural-areas",
        urban_and_rural_folder,
    )
    urban_and_rural = gpd.read_file(urban_and_rural_file)

    # Create USA tamu shapefiles
    grid = Grid("USA")
    sub = create_substation_gdf(grid)
    tamu_loadzones = create_usa_tamu_convex_hull_shapefile(sub, states)

    return translate_zone_set(
        urban_and_rural,
        tamu_loadzones,
        name_prev="urban_and_rural",
        name_new="usa_tamu",
    )
