import pandas as pd

# Apply 2.01kw per person in USA from TAMU paper
load_consumption_per_person = 2.01 / 1000


def compute_load_dist(substation_data, KV_dict):
    """Compute the Pd for each bus based on zip code and population information
    :param pandas.DataFrame substation_data: substation dataframe as returned by :func:`Clean`
    """
    # TODO: first distribute load at zip code level for existing zip codes in HIFLD model

    # distribute load at county level for zip codes not showing in HIFLD substation data
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

    substation_vol = substation_data[["ID", "COUNTYFIPS", "base_KV"]]

    substation_vol_clean = substation_vol.drop(
        substation_vol[substation_vol["base_KV"] < 0].index
    )
    county_sub_total_count = (
        substation_vol_clean.groupby("COUNTYFIPS")
        .size()
        .reset_index(name="total_counts")
    )

    substation_vol_low = substation_vol_clean.drop(
        substation_vol_clean[substation_vol_clean["base_KV"] > 115.0].index
    )
    county_sub_low_kv_count = (
        substation_vol_low.groupby("COUNTYFIPS")
        .size()
        .reset_index(name="low_kv_counts")
    )

    total_count_dict = dict(
        zip(
            county_sub_total_count["COUNTYFIPS"], county_sub_total_count["total_counts"]
        )
    )
    low_kv_count_dict = dict(
        zip(
            county_sub_low_kv_count["COUNTYFIPS"],
            county_sub_low_kv_count["low_kv_counts"],
        )
    )
    load_dict = dict(
        zip(us_county_population["COUNTYFIPS"], us_county_population["load"])
    )

    # if count is less than 10, distribute the load to the substation by load/count

    substation_data["Pd"] = substation_data.apply(
        lambda row: compute_substation_load(
            row, total_count_dict, low_kv_count_dict, load_dict
        ),
        axis=1,
    )

    substation_data["Pd"].fillna(0.0, inplace=True)
    return substation_data


def compute_substation_load(row, total_count_dict, low_kv_count_dict, load_dict):
    if row["base_KV"] < 0:
        return 0
    county_fips = row["COUNTYFIPS"]
    if load_dict.get(county_fips) is None:
        return 0

    if total_count_dict.get(county_fips) < 10:
        return load_dict.get(county_fips) / total_count_dict.get(county_fips)
    elif row["base_KV"] <= 115:
        return load_dict.get(county_fips) / low_kv_count_dict.get(county_fips)
