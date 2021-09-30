import pandas as pd
from powersimdata.utility.distance import haversine

from prereise.gather.griddata.hifld import const
from prereise.gather.griddata.hifld.data_access import load


def floatify(value, default=float("nan")):
    """Return a float if possible, otherwise return a default value.

    :param object value: value to be coerced to float, if possible.
    :param object default: value to be returned if float conversion isn't possible.
    :return: (*float/object*) -- float or default value as applicable.
    """
    try:
        if isinstance(value, str):
            value = value.replace(",", "")
        return float(value)
    except Exception:
        return default


def map_generator_to_sub_by_location(generator, substation_groupby):
    """Determine a likely substation for a generator to be connected to. Priority order
    of mapping is: 1) if location is available and one or more substations exist in that
    ZIP code, map by location to closest substation within that ZIP code, 2) if location
    is available but no substations exist in that ZIP code, map to the closest
    substation within neighboring ZIP codes, 3) if only ZIP code is available
    (no location), and one or more substations exist, map to an arbitrarily chosen
    substation within that ZIP code, 4) if only ZIP code is available (no location)
    but no substations exist in that ZIP code, return NA.

    :param pandas.Series generator: one generating unit from data frame.
    :param pandas.GroupBy substation_groupby: data frame of substations, grouped by
        (interconnect, ZIP).
    :return: (*int/pd.NA*) -- substation ID if the generator can be mapped successfully
        to a substation, else pd.NA.
    """
    lookup_params = tuple(generator.loc[["interconnect", "ZIP"]])
    if pd.isna(generator["lat"]) or pd.isna(generator["lon"]):
        # No location available
        try:
            matching_subs = substation_groupby.get_group(lookup_params)
            return matching_subs.index[0]
        except KeyError:
            return pd.NA
    try:
        # This ZIP code contains substations, this block will execute successfully
        matching_subs = substation_groupby.get_group(lookup_params)
    except KeyError:
        # If this ZIP code does not contain substations, this block will execute, and
        # we select a set of 'nearby' substations
        zip_range = [int(generator.loc["ZIP"]) + offset for offset in range(-100, 101)]
        zip_range_strings = [str(z).rjust(5, "0") for z in zip_range]
        try:
            matching_subs = pd.concat(
                [
                    substation_groupby.get_group((generator.loc["interconnect"], z))
                    for z in zip_range_strings
                    if (generator.loc["interconnect"], z) in substation_groupby.groups
                ]
            )
        except ValueError:
            # If no matching subs within the given interconnection and ZIPs, give up
            return pd.NA
    distance_to_subs = matching_subs.apply(
        lambda x: haversine((x.LATITUDE, x.LONGITUDE), (generator.lat, generator.lon)),
        axis=1,
    )
    return distance_to_subs.idxmin()


def map_generator_to_bus_by_sub(generator, bus_groupby):
    """Determine a likely bus for a generator to be connected to, based on the bus with
    the lowest voltage within the generator's specified substation.

    :param pandas.Series generator: one generating unit from data frame.
    :param pandas.GroupBy bus_groupby: data frame of buses, grouped by substation ID.
    :return: (*int/pd.NA*) -- bus ID if the generator has a substation ID, else pd.NA.
    """
    if pd.isna(generator.sub_id):
        return pd.NA
    else:
        return bus_groupby.get_group(generator.sub_id)["baseKV"].idxmin()


def build_plant(bus, substations):
    """Use source data on generating units from EIA/EPA, along with transmission network
    data, to produce a plant data frame.

    :param pandas.DataFrame bus: data frame of buses, to be used within
        :func:`map_generator_to_bus_by_sub`.
    :param pandas.DataFrame substations: data frame of substations.
    :return: (*pandas.DataFrame*) -- data frame of generator data.
    """
    # Initial loading
    generators = load.get_eia_form_860(const.blob_paths["eia_form860_2019_generator"])
    plants = load.get_eia_form_860(const.blob_paths["eia_form860_2019_plant"])

    # Data interpretation
    plants = plants.set_index("Plant Code")
    plants["Latitude"] = plants["Latitude"].map(floatify)
    plants["Longitude"] = plants["Longitude"].map(floatify)
    for col in ["Summer Capacity (MW)", "Winter Capacity (MW)", "Minimum Load (MW)"]:
        generators[col] = generators[col].map(floatify)

    # Filtering / Grouping
    generators = generators.query(
        "Technology not in @const.eia_storage_gen_types"
    ).copy()
    bus_groupby = bus.groupby(bus["sub_id"].astype(int))
    # Filter substations with no buses
    substations = substations.loc[set(bus_groupby.groups.keys())]
    substation_groupby = substations.groupby(["interconnect", "ZIP"])

    # Add information
    generators["interconnect"] = (
        generators["Plant Code"]
        .map(plants["NERC Region"])
        .map(const.nercregion2interconnect)
    )
    generators["lat"] = generators["Plant Code"].map(plants["Latitude"])
    generators["lon"] = generators["Plant Code"].map(plants["Longitude"])
    generators["ZIP"] = generators["Plant Code"].map(plants["Zip"])
    print("Mapping generators to substations... (this may take several minutes)")
    generators["sub_id"] = generators.apply(
        lambda x: map_generator_to_sub_by_location(x, substation_groupby), axis=1
    )
    generators["bus_id"] = generators.apply(
        lambda x: map_generator_to_bus_by_sub(x, bus_groupby), axis=1
    )
    generators["Pmax"] = generators[
        ["Summer Capacity (MW)", "Winter Capacity (MW)"]
    ].max(axis=1)
    generators.rename({"Minimum Load (MW)": "Pmin"}, inplace=True, axis=1)

    return generators
