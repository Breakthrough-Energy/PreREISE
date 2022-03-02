import folium
from folium.features import DivIcon
import geopandas as gpd
import numpy as np
import pandas as pd

# IMPORTANT: rtree is required for overlay function, but not imported


def plot_zone_map(gdf, interactive=False):
    """Plot map of zones as choropleth. Has 20 colors; buckets zones in
    alphabetical order

    :param geopandas.geodataframe.GeoDataFrame gdf: GeoDataFrame with
        index = zone names, columns = ['geometry']
    :param bool interactive: highlights zone and shows tooltip on hover. Useful
        for identifying zones that have disjoint segments, e.g. LRZ1
    :return: (*matplotlib.axes._subplots.AxesSubplot OR folium.folium.Map*) --
        matplotlib is for non-interactive, folium is interactive
    """
    gdf = gdf.copy()
    gdf["coords"] = gdf["geometry"].apply(lambda x: x.representative_point().coords[:])
    gdf["coords"] = [coords[0] for coords in gdf["coords"]]

    if interactive:
        gdf["zone"] = gdf.index
        interactive_map = gdf.explore(
            column="zone",  # make choropleth based on "zone" column
            tooltip="zone",
            tiles=None,
            style_kwds=dict(color="white", weight=0.7),  # white outline
            legend=False,
        )

        for idx, row in gdf.iterrows():
            coords = list(row["coords"])
            coords.reverse()

            folium.map.Marker(
                coords,
                # add labels
                icon=DivIcon(
                    html=f'<div style="font-size: 8pt; transform: translate(-50%, -50%)">{idx}</div>'
                ),
            ).add_to(interactive_map)

        return interactive_map

    else:
        plt = gdf.plot(
            figsize=(50, 50), linewidth=1, edgecolor="white", cmap="tab20", alpha=0.66
        )

        for idx, row in gdf.iterrows():
            plt.annotate(s=idx, xy=row["coords"], horizontalalignment="center")

        return plt


def filter_interesting_zones(df, rounding=3):
    """Locate all rows and cols that include values that are not 1 or 0

    :param pandas.DataFrame df: matrix of zone_set_a x zone_set_b
    :param int rounding: round all values
    :return: (*pandas.DataFrame*) -- subset of original matrix
    """
    df_copy = df.round(rounding)
    df_copy = df_copy.replace({1.0: 0.0})
    df_copy.loc["sum"] = df_copy.sum()  # sum each col
    df_copy["sum"] = df_copy.sum(axis=1)  # sum each row

    interesting_zones = df_copy.loc[df_copy["sum"] > 0, df_copy.loc["sum"] > 0]
    interesting_zones = interesting_zones.drop(index=["sum"], columns=["sum"])
    interesting_zones = interesting_zones.replace({0.0: "-"})

    return interesting_zones


def format_zone_df(df, name):
    """copies df, checks if it contains valid geometry, and adds col for zone area

    :param geopandas.geodataframe.GeoDataFrame df: GeoDataFrame where
        index = zone names, columns = ['geometry']
    :param str name: the name of the data set
    :return: (*geopandas.geodataframe.GeoDataFrame*) -- the formatted df
    """
    df_copy = df.copy()

    # Check for invalid geometries
    is_valid_df = df_copy.geometry.is_valid.to_frame()
    invalid_geom = list(is_valid_df.loc[is_valid_df[0] == False].index)
    if len(invalid_geom) > 0:
        print(f"WARNING: {name} contains invalid geometries: {invalid_geom}")

    df_copy.index.name = name
    df_copy = df_copy.reset_index()

    # get zone area
    df_copy[f"{name}_area"] = df_copy["geometry"].area

    return df_copy


def translate_zone_set(
    prev_zones, new_zones, name_prev="prev_zones", name_new="new_zones", verbose=False
):
    """returns matrix of prev_zones to new_zones. Scales rows proportionally so
    that each row adds up to 1
    NOTE: We recommend using EPSG:4269 as your CRS (coordinate reference system).
    It triggers a warning but it is able to handle invalid geometries, unlike
    Mercator Projections (EPSG:3395).

    :param geopandas.geodataframe.GeoDataFrame prev_zones: GeoDataFrame with
        index = zone names, columns = ['geometry']
    :param geopandas.geodataframe.GeoDataFrame new_zones: GeoDataFrame with
        index = zone names, columns = ['geometry']
    :param str name_prev: name of the first data set
    :param str name_new: name of the second data set
    :param bool verbose: adds extra print statements for debugging data issues
    :return: (*pandas.DataFrame*) -- matrix of prev_zones to new_zones
    """
    if verbose:
        print(f"ZONES: {name_prev}")
        print(prev_zones)
        print(f"\nZONES: {name_new}")
        print(new_zones)
        print()

    if prev_zones.crs != new_zones.crs:
        print("WARNING: GeoDataFrame CRS does not match. We recommend using EPSG:4269")

    prev_zones = format_zone_df(prev_zones, name_prev)
    new_zones = format_zone_df(new_zones, name_new)

    # get overlapping areas as new polygons
    # this drops areas of new zones that do not overlap prev zones
    # dropped areas will be re-added at the end this function
    prev_overlapped_by_new = prev_zones.overlay(
        new_zones, how="identity", keep_geom_type=False
    )

    # calculate area of overlap as a percentage of the original shape
    prev_overlapped_by_new["overlap_area"] = prev_overlapped_by_new["geometry"].area
    prev_overlapped_by_new["pct_of_prev_area"] = (
        prev_overlapped_by_new["overlap_area"]
        / prev_overlapped_by_new[f"{name_prev}_area"]
    )

    # pivots dataframe into a matrix where rows=prev_zones and cols=new_zones
    prev_to_new_matrix = prev_overlapped_by_new.pivot(
        index=name_prev, columns=name_new, values="pct_of_prev_area"
    )

    # clean NaNs
    prev_to_new_matrix = prev_to_new_matrix.rename(columns={np.nan: "none"})
    prev_to_new_matrix = prev_to_new_matrix.fillna(value=0)

    # check for prev_zones that do not overlap new_zones, then remove
    isolated_zones = prev_to_new_matrix.loc[prev_to_new_matrix["none"] >= 1]
    if len(isolated_zones > 0):
        print(
            f"\nWARNING: Detected {name_prev} zones that do not overlap with {name_new}: {list(isolated_zones.index)}"
        )
        prev_to_new_matrix = prev_to_new_matrix.loc[prev_to_new_matrix["none"] < 1]

    # Alert if sum > 1 (e.g. new zones overlap each other)
    # NOTE: only checks to three decimal places
    prev_to_new_matrix["sum"] = prev_to_new_matrix.sum(axis=1)
    sum_greater_than_one = prev_to_new_matrix.loc[
        prev_to_new_matrix["sum"].round(3) > 1
    ]
    if len(sum_greater_than_one > 0):
        print(
            f"WARNING: Detected rows with a sum greater than one. This most likely means that several {name_new} zones overlap each other."
        )
        if verbose:
            print("\nROWS WITH SUM GREATER THAN ONE:")
        if verbose:
            print(sum_greater_than_one.round(3))

    # Scale matrix such that all rows add up to 1 by distributing demand mismatch
    # proportionally between new zones.
    # if new zones overlap each other, we may end up with > 100% coverage of old zones
    # if old zones aren't completely covered by new zones, we have < 100% coverage
    # Note: we could technically simplify this to just scale_factor = 1/(sum - none) but
    # the extra cols are nice for verbose mode
    prev_to_new_matrix["sum_without_none"] = (
        prev_to_new_matrix["sum"] - prev_to_new_matrix["none"]
    )
    prev_to_new_matrix["to_distribute"] = 1 - prev_to_new_matrix["sum_without_none"]
    prev_to_new_matrix["scale_factor"] = (
        1 + prev_to_new_matrix["to_distribute"] / prev_to_new_matrix["sum_without_none"]
    )

    if verbose:
        print("\nMATRIX BEFORE SCALING")
    if verbose:
        print(prev_to_new_matrix.round(3))

    scaled_matrix = prev_to_new_matrix.mul(
        prev_to_new_matrix["scale_factor"], axis="rows"
    )
    scaled_matrix = scaled_matrix.drop(
        columns=["none", "sum", "sum_without_none", "to_distribute", "scale_factor"]
    )

    # Add any rows that got dropped because they do not overlap. Fill with zeros.
    # NOTE: not sure if this will get slow with larger datasets
    if len(scaled_matrix) < len(prev_zones):
        index = scaled_matrix.index.values
        for zone in list(prev_zones[name_prev]):
            if not zone in index:
                scaled_matrix.loc[zone] = 0

    # Similarly, add missing columns
    if len(scaled_matrix.columns) < len(new_zones):
        columns = scaled_matrix.columns
        for zone in list(new_zones[name_new]):
            if not zone in columns:
                scaled_matrix[zone] = 0

    if verbose:
        print(
            "\nINTERESTING ZONES: rows and cols that include values that are not 1 or 0"
        )
        with pd.option_context("display.max_rows", None, "display.max_columns", None):
            print(filter_interesting_zones(scaled_matrix))

    return scaled_matrix
