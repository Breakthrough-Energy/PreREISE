import json
import os
import shutil

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import requests

from prereise.gather.data.remap_ba_area.map_data import (
    miso_name_map,
    spp_name_map,
    states_to_map_with_counties,
)


def get_full_filename(file_name):
    return os.path.join(os.path.dirname(__file__), file_name)


def compose_ba_map(output_shape_file="remap_ba_area.shp"):
    """
    Create the control area and subregion map. For CAs heavily overlapped, we define several zones and match the CAs to
    these zones. The ca_source name is either mapped to one zone in BA_map_name, or allocated to multiple zones in
    BA_map_name with fractions based on the area.
    The function generates the remap_ba_area shape file and remap_ba_area.tif file.

    :param str output_shape_file: output shape file name
    :return: (*geopandas.GeoDataFrame*)  -- the final control zone map
    """

    with open(get_full_filename("../BA_County_map.json"), encoding="UTF8") as json_file:
        ba2county_dict = json.load(json_file)

    # Turn dict into pandas table
    county2ba_dict = {
        county: ba
        for (ba, ba_counties) in ba2county_dict.items()
        for county in ba_counties
    }
    county2ba = pd.Series(county2ba_dict).to_frame().reset_index()
    county2ba.columns = ["index", "BA"]
    county2ba[["county", "state"]] = county2ba["index"].str.split(
        "__", n=1, expand=True
    )
    county2ba = county2ba.drop(columns=["index"])
    county2ba.set_index(["county", "state"], inplace=True)

    # US Counties Shapefile
    counties_shp_file = gpd.read_file(get_full_filename("cb_2020_us_county_500k.zip"))
    # Remove AK, HI, PR, etc.
    counties_shp_file = counties_shp_file[["NAME", "STUSPS", "geometry"]].rename(
        columns={"NAME": "county", "STUSPS": "state"}
    )
    lower48 = counties_shp_file.loc[
        counties_shp_file["state"].isin(states_to_map_with_counties)
    ]
    lower48.set_index(["county", "state"], inplace=True)
    counties_with_ba = lower48.join(county2ba)

    # Aggregate counties into BA
    ba_dissolved = counties_with_ba.dissolve(by="BA")["geometry"].to_frame()
    # Drop PJM, replace with alternate shapes
    ba_dissolved.drop("PJM", inplace=True)
    pjm = gpd.read_file(get_full_filename("pjm.zip")).set_index("BA")
    ba_dissolved = pd.concat([ba_dissolved, pjm])
    california = gpd.read_file(
        os.path.join(os.path.dirname(__file__), "CA_balancing_authorities.zip")
    )

    # Align California's name for PacifiCorp West with the county-based BA name
    california.loc[california["NAME"] == "PacificCorp West", "NAME"] = "PACW"
    california = california.set_index("NAME")
    california.index.name = "BA"

    # Change coordinate reference system to match county data
    california = california.to_crs(4269)
    # Remove CAISO, since we'll use a different source for CAISO shapes
    california = california.loc[~california.index.isin({"CALISO"})]
    hifld_utilities = gpd.read_file(
        get_full_filename("Electric_Retail_Service_Territories.zip")
    )

    balancing_authorities = {
        "ANZA ELECTRIC COOP INC": "WAPA",
        "TRINITY PUBLIC UTILITIES DIST": "BANC",
    }

    caiso_subregion_names = {
        "SAN DIEGO GAS & ELECTRIC CO": "CISO-SDGE",
        "VALLEY ELECTRIC ASSN, INC": "CISO-VEA",
        # PG&E proper & friends
        "PACIFIC GAS & ELECTRIC CO.": "CISO-PGAE",
        "CITY OF HEALDSBURG - (CA)": "CISO-PGAE",
        "CITY OF LODI - (CA)": "CISO-PGAE",
        "CITY OF LOMPOC - (CA)": "CISO-PGAE",
        "CITY OF PALO ALTO - (CA)": "CISO-PGAE",
        "CITY OF SANTA CLARA - (CA)": "CISO-PGAE",
        "CITY OF UKIAH - (CA)": "CISO-PGAE",
        "LASSEN MUNICIPAL UTILITY DISTRICT": "CISO-PGAE",
        "PLUMAS-SIERRA RURAL ELEC COOP": "CISO-PGAE",
        # SCE proper & friends
        "SOUTHERN CALIFORNIA EDISON CO": "CISO-SCE",
        "BEAR VALLEY ELECTRIC SERVICE": "CISO-SCE",
        "CITY OF ANAHEIM - (CA)": "CISO-SCE",
        "CITY OF AZUSA": "CISO-SCE",
        "CITY OF BANNING - (CA)": "CISO-SCE",
        "CITY OF COLTON - (CA)": "CISO-SCE",
        "CITY OF MORENO VALLEY - (CA)": "CISO-SCE",
        "CITY OF PASADENA - (CA)": "CISO-SCE",
        "CITY OF RIVERSIDE - (CA)": "CISO-SCE",
        "CITY OF VERNON": "CISO-SCE",
        "CITY OF VICTORVILLE - (CA)": "CISO-SCE",
    }

    utility_mapping = {**balancing_authorities, **caiso_subregion_names}
    caiso_subregions = hifld_utilities.loc[
        hifld_utilities["NAME"].isin(utility_mapping)
    ].copy()
    caiso_subregions["NAME"] = caiso_subregions["NAME"].map(utility_mapping)
    caiso_subregions.rename({"NAME": "BA"}, axis="columns", inplace=True)
    # Tag the existing geometries with their true CRS, then re-project
    caiso_subregions = caiso_subregions.set_crs(3857, allow_override=True)
    caiso_subregions = caiso_subregions.to_crs(4269)
    california_joined = pd.concat([california.reset_index(), caiso_subregions])
    # We simultaneously concatenate and dissolve
    full_ba_map = (
        pd.concat([ba_dissolved.reset_index(), california_joined])
        .dissolve(by="BA")["geometry"]
        .to_frame()
    )
    # Subtract the CAISO Valley Electric Association geometry from the Nevada Power geometry
    full_ba_map.loc["NEVP", "geometry"] = full_ba_map.loc[
        "NEVP", "geometry"
    ].difference(full_ba_map.loc["CISO-VEA", "geometry"])

    nyiso = get_nyiso_area(crs=full_ba_map.crs)
    full_ba_map = pd.concat([full_ba_map, nyiso])
    # add ISONE
    full_ba_map = full_ba_map.drop("ISNE")
    isone_df = get_isone()
    isone_df = isone_df.assign(BA=isone_df["BA"].apply(lambda t: "ISONE-" + t))
    full_ba_map = pd.concat([full_ba_map, isone_df.set_index("BA")])
    # assign the four utility territories into existing CA/subregion
    # rename TVA_LGEE to TVA, to match the source name
    extra_map = {
        "NV Energy": "CISO-PGAE",
        "SCL_TPWR": "BPAT",
        "WAPA": "CISO-SCE",
        "TVA_LGEE": "TVA",
    }
    full_ba_map = full_ba_map.reset_index().replace({"BA": extra_map}).set_index("BA")
    full_ba_map = full_ba_map.dissolve(by="BA")

    rows = full_ba_map.shape[0]
    name_map = {**miso_name_map, **spp_name_map}
    full_ba_map.reset_index(inplace=True)
    full_ba_map["BA"].replace(name_map, inplace=True)
    full_ba_map.to_file(get_full_filename(output_shape_file))
    full_ba_map.assign(id=range(rows)).plot(
        categorical=True, column="id", cmap="Accent", edgecolor="black"
    )

    plt.savefig(get_full_filename("remap_ba_area.tif"))
    print("BA map completed!")

    return full_ba_map


def get_nyiso_area(crs, nydir=get_full_filename("nyiso")):
    """
    Load the NYISO map from the kml files and the geojson file into a geo dataframe.

    :param  pyproj.CRS crs: coordinate reference system
    :param str nydir: NYISO map folder
    :return: (*geopandas.GeoDataFrame*)  -- NYISO geoDataFrame
    """
    files = os.listdir(nydir)
    gpd.io.file.fiona.drvsupport.supported_drivers["KML"] = "rw"
    df_list = []
    for f in files:
        if f.endswith("kml"):
            df = gpd.read_file(os.path.join(nydir, f), driver="KML")
            df_list.append(df.to_crs(crs))
        elif f.endswith("geojson"):
            df = gpd.read_file(os.path.join(nydir, f))
            df = df.rename(columns={"NAME": "Name"})
            df = df[["Name", "geometry"]]

            df_list.append(df.to_crs(crs))

    df = pd.concat(df_list)
    df_b = df.set_index("Name").loc[["Zone B one", "Zone B two"]].dissolve()
    df_b["Name"] = "Zone B"
    df_rest = df.set_index("Name").drop(["Zone B one", "Zone B two"]).reset_index()
    df = pd.concat([df_b, df_rest])
    del df["Description"]
    df = df.rename(columns={"Name": "BA"})
    col_names = {
        "Zone A": "NYISO-A",
        "Zone B": "NYISO-B",
        "Zone C": "NYISO-C",
        "Zone D": "NYISO-D",
        "Zone E": "NYISO-E",
        "Zone F": "NYISO-F",
        "Zone G": "NYISO-G",
        "Millwood": "NYISO-H",
        "Dunwoodie": "NYISO-I",
        "Long Island": "NYISO-K",
        "N.Y.C": "NYISO-J",
    }
    df["BA"] = df["BA"].map(col_names)
    return df.set_index("BA")


def download_nyiso_map():
    """
    Download the upper NYISO kml file.

    :return: (*None*)
    """
    url_dict = {
        "Zone_A.kml": "https://www.arcgis.com/sharing/rest/content/items/52b8452f80fb4c378a96b382e6c88552/data",
        "Zone_B_one.kml": "https://www.arcgis.com/sharing/rest/content/items/d0d89f78c77241b482731665e2886941/data",
        "Zone_B_two.kml": "https://www.arcgis.com/sharing/rest/content/items/1897cf65493a4a76aefba16779df75e8/data",
        "Zone_C.kml": "https://www.arcgis.com/sharing/rest/content/items/203cf0c4c66c451bb8f220d685bffba8/data",
        "Zone_D.kml": "https://www.arcgis.com/sharing/rest/content/items/285908f3114547cabb8733ec53883d0b/data",
        "Zone_E.kml": "https://www.arcgis.com/sharing/rest/content/items/ff3bd2344555499cb1c794a2364eec60/data",
        "Zone_F.kml": "https://www.arcgis.com/sharing/rest/content/items/19867671655e4db6906a8b7a6b810123/data",
        "Zone_G.kml": "https://www.arcgis.com/sharing/rest/content/items/a515e6d248db4043b24b9bfd56d0f0ab/data",
    }
    for fn in url_dict:
        response = requests.get(url_dict[fn], stream=True)
        nyiso_folder = "nyiso"
        with open(
            f"{get_full_filename(os.path.join(nyiso_folder, fn))}", "wb"
        ) as out_file:
            shutil.copyfileobj(response.raw, out_file)


def get_isone():
    isone_zone = [
        "New Hampshire",
        "Massachusetts",
        "New Hampshire",
        "Rhode Island",
        "Vermont",
        "Maine",
        "Connecticut",
    ]
    counties_shp = gpd.read_file(
        os.path.join(os.path.dirname(__file__), "cb_2020_us_county_500k.zip")
    )[["STATE_NAME", "geometry"]]
    c = counties_shp[["STATE_NAME", "geometry"]].dissolve(by="STATE_NAME")
    return c.loc[isone_zone].reset_index().rename(columns={"STATE_NAME": "BA"})


def main():
    download_nyiso_map()
    compose_ba_map()


if __name__ == "__main__":
    main()
