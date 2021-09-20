import json
import os
import tempfile
from io import BytesIO
from urllib.parse import urlparse
from urllib.request import urlopen
from zipfile import ZipFile

import pandas as pd
from tqdm import tqdm

from prereise.gather.griddata.hifld.const import abv2state  # noqa: F401
from prereise.gather.griddata.hifld.const import heat_rate_estimation_columns


def get_eia_form_860(path):
    """Read the a CSV file for EIA Form 860 and keep plants located in contiguous
    states.

    :param str path: path to file. Either local or URL.
    :return: (*pandas.DataFrame*) -- operational power plant in contiguous states.
    """
    data = pd.read_csv(path)
    return data.query("State in @abv2state")


def get_epa_ampd(path, year=2019, cache=False):
    """Read a collection of zipped CSV files from the EPA AMPD dataset and keep readings
    from plants located in contiguous states.

    :param str path: path to folder. Either local or URL.
    :param str year: year of data to read (will be present in filenames)
    :param bool cache: Whether to locally cache the EPA AMPD data, and read from the
        cache when it's available.
    :return: (*pandas.DataFrame*) -- readings from operational power plant in contiguous
        states.
    """
    # Determine whether paths should be joined with os separators or URL separators
    try:
        result = urlparse(path)
        if result.scheme in {"http", "ftp", "s3", "file"}:
            path_sep = "/"
        else:
            path_sep = os.path.sep
    except Exception:
        raise ValueError(f"Could not interpret path {path}")
    # Trim trailing slashes as necessary to ensure that join works
    path = path.rstrip("/\\")

    # Build cache path if necessary
    if cache:
        cache_dir = os.path.join(os.path.dirname(__file__), "cache")
        os.makedirs(cache_dir, exist_ok=True)

    data = {state: {} for state in abv2state}
    for state in tqdm(abv2state):
        for month_num in range(1, 13):
            filename = f"{year}{state.lower()}{str(month_num).rjust(2, '0')}.zip"
            if cache:
                try:
                    df = pd.read_csv(
                        os.path.join(cache_dir, filename),
                        usecols=heat_rate_estimation_columns,
                    )
                except Exception:
                    df = pd.read_csv(
                        path_sep.join([path, filename]),
                        usecols=heat_rate_estimation_columns,
                    )
                    df.to_csv(
                        os.path.join(cache_dir, filename),
                        compression={
                            "method": "zip",
                            "archive_name": filename.replace(".zip", ".csv"),
                        },
                    )
            else:
                df = pd.read_csv(
                    path_sep.join([path, filename]),
                    usecols=heat_rate_estimation_columns,
                )
            data[state][month_num] = df
    joined = pd.concat(
        [data[state][month_num] for state in abv2state for month_num in range(1, 13)]
    )

    return joined.astype({"UNITID": "string"})


def get_epa_needs(path):
    """Read the a CSV file for an EPA NEEDS dataset and keep plants located in
    contiguous states.

    :param str path: path to file. Either local or URL.
    :return: (*pandas.DataFrame*) -- operational power plant in contiguous states.
    """
    data = pd.read_csv(path)
    return data.query("`State Name` in @abv2state.values()")


def get_hifld_power_plants(path):
    """Read the HIFLD Power Plants CSV file and keep operational plants located in
    contiguous states.

    :param str path: path to file. Either local or URL.
    :return: (*pandas.DataFrame*) -- operational power plant in contiguous states.
    """
    data = (
        pd.read_csv(path)
        .astype(
            {
                "SOURCEDATE": "datetime64",
                "VAL_DATE": "datetime64",
            }
        )
        .rename(columns={"SOURC_LONG": "SOURCE_LON"})
        .drop(columns=["OBJECTID"])
    )
    return data.query("STATUS == 'OP' and STATE in @abv2state")


def get_hifld_generating_units(path):
    """Read the HIFLD Generating Units CSV file and keep operational plants located in
    contiguous states.

    :param str path: path to file. Either local or URL.
    :return: (*pandas.DataFrame*) -- operational generating units in contiguous states.
    """
    data = (
        pd.read_csv(path)
        .astype({"SOURCEDATE": "datetime64"})
        .drop(columns=["OBJECTID"])
    )
    return data.query("STATUS == 'OP' and STATE in @abv2state")


def get_hifld_electric_substations(path):
    """Read the HIFLD Electric Substations CSV file and keep in service substations
    located in contiguous states and connected to at least one transmission line.

    :param str path: path to file. Either local or URL.
    :return: (*pandas.DataFrame*) -- in service electric substations in contiguous
        states that are connected to at least one electric power transmission line.
    """
    data = (
        pd.read_csv(path)
        .drop(columns=["OBJECTID"])
        .round({"MAX_VOLT": 3, "MIN_VOLT": 3})
    )

    return data.query("STATUS == 'IN SERVICE' and STATE in @abv2state")


def get_hifld_electric_power_transmission_lines(path):
    """Read the HIFLD Electric Power Transmission Lines json zip file and keep in
    service lines.

    :param str path: path to zip file. Either local or URL.
    :return: (*pandas.DataFrame*) -- each element is a dictionary enclosing the
        information of the electric power transmission line along with its topology.
    """
    dir = tempfile.TemporaryDirectory()
    if path[:4] == "http":
        with urlopen(path) as zipresp:
            with ZipFile(BytesIO(zipresp.read())) as zipfile:
                zipfile.extractall(os.path.join(dir.name, "topology"))
    else:
        with ZipFile(path, "r") as zipfile:
            zipfile.extractall(os.path.join(dir.name, "topology"))

    fp = os.path.join(dir.name, "topology", "Electric_Power_Transmission_Lines.geojson")
    with open(fp, "r", encoding="utf8") as f:
        data = json.load(f)
    dir.cleanup()

    properties = (
        pd.DataFrame([line["properties"] for line in data["features"]])
        .astype({"ID": "int64", "NAICS_CODE": "int64", "SOURCEDATE": "datetime64"})
        .drop(columns=["OBJECTID", "SHAPE_Length"])
        .round({"VOLTAGE": 3})
    )

    properties["COORDINATES"] = [
        line["geometry"]["coordinates"][0] for line in data["features"]
    ]
    # Flip [(lon, lat), (lon, lat), ..] points to [(lat, lon), (lat, lon), ...]
    properties["COORDINATES"] = properties["COORDINATES"].map(
        lambda x: [y[::-1] for y in x]
    )

    # Replace dummy data with explicit 'missing'
    properties.loc[properties.VOLTAGE == -999999, "VOLTAGE"] = pd.NA

    return properties.query("STATUS == 'IN SERVICE'")


def get_zone(path):
    """Read zone CSV file.

    :param str path: path to file. Either local or URL.
    :return: (*pandas.DataFrame*) -- information related to load zone
    """
    return pd.read_csv(path, index_col="zone_id")
