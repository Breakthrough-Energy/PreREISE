import pandas as pd

# Apply 2.01kw per person in USA from TAMU paper
load_consumption_per_person = 2.01 / 1000

# Special case for NYC area: aggregate the neighbor counties
# NYC COUNTYFIPS:
# 36081 (Queens), 36047 (Kings), 36005 (Bronx)
# 36085 (Richmond), 36061 (NewYork), 36119 (Westchester), 36059 (Nassau)
nyc_countyfips = set(["36047", "36005", "36085", "36061"])


def compute_load_dist(substation_data, KV_dict):
    """Compute the Pd for each bus based on zip code and population information
    :param pandas.DataFrame substation_data: substation dataframe loaded from HIFLD raw data after clean-up
    :param dict KV_dict: a dict of substation's baseKV value.
    :return pandas.DataFrame substation_data: substation dataframe with pd column computed and added
    """

    # Firstly distribute load at zip code level for existing zip codes in HIFLD model
    us_zip_population = pd.read_csv(
        "data/uszips.csv",
        dtype={"zip": str, "population": str},
        usecols=["zip", "population"],
    )
    us_zip_population["population"] = (
        us_zip_population["population"].fillna(0)
    ).astype(int)
    us_zip_population["load"] = (
        us_zip_population["population"] * load_consumption_per_person
    )

    # Also need to distribute load at county level for zip codes not showing in HIFLD substation raw data
    us_county_population = pd.read_csv(
        "data/uscounties.csv",
        dtype={"county_fips": str, "population": int},
        usecols=["county_fips", "population"],
    )
    us_county_population["load"] = (
        us_county_population["population"] * load_consumption_per_person
    )
    us_county_population = us_county_population.rename(
        {"county_fips": "COUNTYFIPS"}, axis="columns"
    )

    substation_data["base_KV"] = substation_data.apply(
        lambda row: KV_dict.get((row["LATITUDE"], row["LONGITUDE"])), axis=1
    )

    substation_vol = substation_data[["ID", "COUNTYFIPS", "base_KV", "ZIP"]]

    substation_vol_clean = substation_vol.drop(
        substation_vol[substation_vol["base_KV"] < 0].index
    )

    county_load_dict = dict(
        zip(us_county_population["COUNTYFIPS"], us_county_population["load"])
    )

    zip_sub_total_count = (
        substation_vol_clean.groupby("ZIP").size().reset_index(name="total_counts")
    )
    zip_total_count_dict = dict(
        zip(zip_sub_total_count["ZIP"], zip_sub_total_count["total_counts"])
    )
    zip_load_dict = dict(zip(us_zip_population["zip"], us_zip_population["load"]))
    zip_load_assigned_dict = dict(
        zip(us_zip_population["zip"], us_zip_population["load"] * 0)
    )
    substation_data = substation_data.sort_values(by=["LINES"], ascending=False)
    substation_data["Pd_zip"] = substation_data.apply(
        lambda row: compute_substation_load_by_zip(
            row,
            zip_total_count_dict,
            zip_load_dict,
            zip_load_assigned_dict,
            county_load_dict,
        ),
        axis=1,
    )
    substation_data = substation_data.sort_values(by=["OBJECTID"])

    load_substation = substation_data[substation_data["Pd_zip"] > 0][
        ["ID", "COUNTYFIPS"]
    ]

    county_load_sub_total_count = (
        load_substation.groupby("COUNTYFIPS").size().reset_index(name="total_counts")
    )
    county_load_sub_total_count_dict = dict(
        zip(
            county_load_sub_total_count["COUNTYFIPS"],
            county_load_sub_total_count["total_counts"],
        )
    )

    substation_data["Pd_county"] = substation_data.apply(
        lambda row: compute_substation_load_by_county(
            row, county_load_sub_total_count_dict, county_load_dict
        ),
        axis=1,
    )

    substation_data["Pd_county"].fillna(0.0, inplace=True)
    substation_data["Pd"] = substation_data["Pd_zip"] + substation_data["Pd_county"]
    return substation_data


def compute_substation_load_by_county(
    row, county_load_sub_total_count_dict, county_load_dict
):
    """Compute the load for each substation based on its COUNTY population information
    :param pandas.DataFrame.row: one row in the substation dataframe
    :param dict county_load_sub_total_count_dict: a dict of substation count in each county
    :param dict county_load_dict: a dict of county's load
    :return float: the load allocated to this substation
    """

    if row["base_KV"] < 0 or row["Pd_zip"] <= 0:
        return 0
    county_fips = row["COUNTYFIPS"]
    if county_fips in nyc_countyfips:
        return 0
    if (
        county_load_dict.get(county_fips) is None
        or county_load_dict.get(county_fips) <= 0
    ):
        return 0

    return county_load_dict.get(county_fips) / county_load_sub_total_count_dict.get(
        county_fips
    )


def compute_substation_load_by_zip(
    row, zip_total_count_dict, zip_load_dict, zip_load_assigned_dict, county_load_dict
):
    """Compute the load for each substation based on its ZIP code population information
    :param pandas.DataFrame.row: one row in the substation dataframe
    :param dict zip_total_count_dict: a dict of substation count in each zip
    :param dict zip_load_dict: a dict of zip's total load
    :param dict zip_load_assigned_dict: a dict of allocated load for each zip
    :param dict county_load_dict: a dict of county's total load
    :return float: the load allocated to this substation
    """

    if row["base_KV"] < 0:
        return 0
    zip = row["ZIP"]
    if zip_load_dict.get(zip) is None or zip_load_dict.get(
        zip
    ) <= zip_load_assigned_dict.get(zip):
        return 0

    # If there is only one bus in this zip, assign the load to it
    if zip_total_count_dict.get(zip) == 1:
        bus_load = zip_load_dict.get(zip)
    else:
        # Take half of the buses as load bus
        load_bus_size = zip_total_count_dict.get(zip) * 0.6
        bus_load = min(
            zip_load_dict.get(zip) / load_bus_size,
            zip_load_dict.get(zip) - zip_load_assigned_dict.get(zip),
        )

    # Update load_assigned dict so we can stop when load is all assigned out in one zip
    zip_load_assigned_dict[zip] += bus_load

    # Update the county load dict so we only handle the rest of the county-level load
    county_fips = row["COUNTYFIPS"]
    if county_load_dict.get(county_fips) is not None:
        county_load_dict[county_fips] -= bus_load

    return bus_load
