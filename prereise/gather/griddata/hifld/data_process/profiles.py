import datetime as dt

import pandas as pd

from prereise.gather.griddata.hifld import const
from prereise.gather.griddata.hifld.data_access.load import get_eia_form_860
from prereise.gather.hydrodata.eia.fetch_historical import get_generation
from prereise.gather.impute import linear
from prereise.gather.solardata.nsrdb.sam import retrieve_data_individual
from prereise.gather.winddata.hrrr.calculations import calculate_pout_individual
from prereise.gather.winddata.hrrr.hrrr import retrieve_data


def floatify(x):
    """Coerce an object to a float, returning a float NaN for any objects which raise an
    exception when passed to :func:`float`.

    :param object x: object to coerce.
    :return: (*float*) -- coerced value.
    """
    try:
        return float(x)
    except ValueError:
        return float("nan")


def build_solar(solar_plants, nrel_email, nrel_api_key, **solar_kwargs):
    """Use plant-level data to build solar profiles.

    :param pandas.DataFrame solar_plants: data frame of solar farms.
    :param str nrel_email: email used to`sign up <https://developer.nrel.gov/signup/>`_.
    :param str nrel_api_key: API key.
    :param dict solar_kwargs: keyword arguments to pass to
        :func:`prereise.gather.solardata.nsrdb.sam.retrieve_data_individual`.
    :return: (*pandas.DataFrame*) -- data frame of normalized power profiles. The index
        is hourly timestamps for the profile year, the columns are plant IDs, the values
        are floats.
    """
    boolean_columns = ["Single-Axis Tracking?", "Dual-Axis Tracking?", "Fixed Tilt?"]
    float_columns = ["DC Net Capacity (MW)", "Nameplate Capacity (MW)", "Tilt Angle"]
    # Load raw 'extra' table data, join on plant & generating unit, re-establish index
    extra_solar_data = get_eia_form_860(const.blob_paths["eia_form860_2019_solar"])
    full_data = solar_plants.merge(
        extra_solar_data, on=["Plant Code", "Generator ID"], suffixes=(None, "_extra")
    )
    full_data.index = solar_plants.index
    # Process data to expected types for profile generation
    for col in float_columns:
        full_data[col] = full_data[col].map(floatify)
    for col in boolean_columns:
        # 'Y' becomes True, anything else ('N', blank, etc) becomes False
        full_data[col] = full_data[col] == "Y"

    # If panel type isn't known definitively, assume 100% Fixed Tilt
    # Solar thermal also ends up labeled as fixed tilt, but this will be ignored
    bad_booleans = full_data.index[full_data[boolean_columns].sum(axis=1) != 1]
    full_data.loc[bad_booleans, boolean_columns] = False
    full_data.loc[bad_booleans, "Fixed Tilt?"] = True

    full_data.index.name = "plant_id"  # needed for next step but gets lost in the merge
    profiles = retrieve_data_individual(
        nrel_email,
        nrel_api_key,
        solar_plant=full_data,
        **solar_kwargs,
    )
    return profiles


def build_wind(wind_plants, download_directory, year):
    """Use plant-level data to build wind profiles.

    :param pandas.DataFrame wind_plants: data frame of wind farms.
    :param str download_directory: location to download wind speed data to.
    :param int/str year: year of weather data to use for generating profiles.
    :return: (*pandas.DataFrame*) -- data frame of normalized power profiles. The index
        is hourly timestamps for the profile year, the columns are plant IDs, the values
        are floats.
    """
    default_hub_height = 262.467  # (262.467 ft = 80m)
    # Load raw 'extra' table data, join on plant & generating unit, re-establish index
    extra_wind_data = get_eia_form_860(const.blob_paths["eia_form860_2019_wind"])
    full_data = wind_plants.merge(
        extra_wind_data, on=["Plant Code", "Generator ID"], suffixes=(None, "_extra")
    )
    full_data.index = wind_plants.index
    # Process data to expected types for profile generation
    full_data["Turbine Hub Height (Feet)"] = (
        full_data["Turbine Hub Height (Feet)"].map(floatify).fillna(default_hub_height)
    )
    full_data["Predominant Turbine Manufacturer"] = (
        full_data["Predominant Turbine Manufacturer"].astype("string").fillna("")
    )
    full_data["Predominant Turbine Model Number"] = (
        full_data["Predominant Turbine Model Number"].astype("string").fillna("")
    )
    start_dt = dt.datetime.fromisoformat(f"{year}-01-01-00")
    end_dt = dt.datetime.fromisoformat(f"{year}-12-31-23")
    retrieve_data(start_dt=start_dt, end_dt=end_dt, directory=download_directory)
    profiles = calculate_pout_individual(
        wind_farms=full_data,
        start_dt=start_dt,
        end_dt=end_dt,
        directory=download_directory,
    )
    return profiles


def filter_anomalies_impute(series, capacity, rel_min=-1, rel_max=2, max_count=100):
    """Given a time-series of generation and an assumed capacity, identify anomalous
    points and replace them by linear imputation (unless there are too many, in which
    case return a copy of the original.

    :param pandas.Series/numpy.ndarray series: 1-D data to filter and impute (MW).
    :param int/float capacity: assumed capacity (MW).
    :param int/float rel_min: lower screening value (relative to ``capacity``).
    :param int/float rel_max: upper screening value (relative to ``capacity``).
    :param int max_count: the maximum number of anomalies that can be replaced. If more
        than this number exist, the series will be returned as is.
    :return: (*pandas.Series*) -- data, imputed as applicable.
    :raise ValueError: if series isn't a 1-D object
    """
    if len(series.shape) != 1:
        raise ValueError("series must be of one-dimentional shape")
    suspected_anomalies = (series > rel_max * capacity) | (series < rel_min * capacity)
    output = series.copy()
    if suspected_anomalies.sum() == 0:
        return output
    if suspected_anomalies.sum() > max_count:
        print(f"Too many suspected anomalies for {series.name}, none will be filtered")
        return output
    output.loc[suspected_anomalies] = float("nan")
    return linear(output.to_frame(), inplace=False).squeeze()


def parse_eia_to_normalized(hydro_plants, generation, query_regions, year):
    """Given hydro generation profiles (MW) for a set of balancing authorities, create
    profiles which are capacity-normalized for a superset of balancing authorities.
    Profiles are normalized either using the total capacity of the balancing authority's
    hydro capacity or by peak generation, whichever is greater. Balancing authorities
    which are missing from the source generation data are populated using a profile
    aggregated from all available balancing authorities.

    :param pandas.DataFrame hydro_plants: data frame of hydro plant data, including
        columns 'Balancing Authority Code' and 'Pmax'.
    :param pandas.DataFrame generation: data frame of hourly generation. Index is
        timestamps, columns are balancing authority codes, values are total generation.
    :param set query_regions: superset of balacing authority areas to produce profiles
        for.
    :param int/str year: year to use for output profile timestamps.
    :return: (*pandas.DataFrame*) -- index is hourly timestamps for the given year,
        columns are the superset balancing authorities, values are normalized
        generation.
    """
    # Filter generation anomalies based on installed capacity
    ba_groups = hydro_plants.groupby("Balancing Authority Code")
    ba_capacities = ba_groups["Pmax"].sum()

    # Normalize regional totals by regional capacities (or peak generation)
    normalized_by_generation = generation.columns[
        generation.max() > ba_capacities.loc[generation.columns]
    ]
    if len(normalized_by_generation) > 0:
        print("regions normalized by generation profile:")
        print(
            generation[normalized_by_generation].max()
            / ba_capacities.loc[normalized_by_generation]
        )
    normalizing_capacity = pd.concat(
        [ba_capacities.loc[generation.columns], generation.max()],
        axis=1,
    ).max(axis=1)
    normalized_profiles = generation / normalizing_capacity

    # Build shape for 'default' (weighted average of other shapes)
    normalized_profiles["default"] = (
        normalized_profiles * ba_capacities.loc[normalized_profiles.columns]
    ).sum(axis=1) / ba_capacities.loc[normalized_profiles.columns].sum()

    # Build the output dataframe, and populate it
    profiles = pd.DataFrame(
        index=pd.date_range(start=f"{year}-01-01-00", end=f"{year}-12-31-23", freq="H"),
        columns=hydro_plants.index,
    )
    for region in query_regions:
        plant_ids = ba_groups.get_group(region).index
        if region in normalized_profiles:
            template = normalized_profiles[region]
        else:
            print(region, "uses 'default' hydro profile")
            template = normalized_profiles["default"]
        # pandas won't broadcast for us, so we need to construct a 2D object
        profiles.loc[:, plant_ids] = pd.concat(
            [template] * len(plant_ids), axis=1
        ).values

    return profiles


def build_hydro(hydro_plants, eia_api_key, year, **hydro_kwargs):
    """Use plant-level data to build hydro profiles.

    :param pandas.DataFrame hydro_plants: data frame of hydro generators.
    :param str eia_api_key: API key.
    :param int/str year: year of data to fetch and build profiles for.
    :param dict hydro_kwargs: keyword arguments to pass to
        :func:`prereise.gather.hydrodata.eia.fetch_historical.get_generation`.
    :return: (*pandas.DataFrame*) -- data frame of normalized power profiles. The index
        is hourly timestamps for the profile year, the columns are plant IDs, the values
        are floats.
    """
    # Build shapes for each region
    query_regions = set(hydro_plants["Balancing Authority Code"].unique())
    hydro_kwargs["year"] = year
    generation = get_generation(eia_api_key, regions=query_regions, **hydro_kwargs)
    # Initial screen: any points > 2x capacity or < -1 * capacity
    ba_capacities = hydro_plants.groupby("Balancing Authority Code")["Pmax"].sum()
    imputed = generation.apply(
        lambda x: filter_anomalies_impute(x, capacity=ba_capacities.loc[x.name])
    )
    # Normalize
    profiles = parse_eia_to_normalized(hydro_plants, imputed, query_regions, year)

    return profiles
