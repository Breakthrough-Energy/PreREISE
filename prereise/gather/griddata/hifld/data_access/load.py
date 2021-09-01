import json
import os
import tempfile
from io import BytesIO
from urllib.request import urlopen
from zipfile import ZipFile

import pandas as pd

from prereise.gather.griddata.hifld.const import abv2state  # noqa F401


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

    # Replace dummy data with explicit 'missing'
    properties.loc[properties.VOLTAGE == -999999, "VOLTAGE"] = pd.NA

    return properties.query("STATUS == 'IN SERVICE'")


def get_zone(path):
    """Read zone CSV file.

    :param str path: path to file. Either local or URL.
    :return: (*pandas.DataFrame*) -- information related to load zone
    """
    return pd.read_csv(path, index_col="zone_id")
