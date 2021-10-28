import pandas as pd

from prereise.gather.griddata.hifld import const
from prereise.gather.griddata.hifld.data_access.load import get_us_counties, get_us_zips


def assign_demand_to_buses(substations, branch, plant, bus):
    """Using data on population by county and ZIP code, assign demand to substations,
    then to the lowest-voltage bus within each substation.
    This demand parameter is added inplace as a 'Pd' column to the ``bus`` data frame.

    :param pandas.DataFrame substations: table of substation data.
    :param pandas.DataFrame branch: table of branch data.
    :param pandas.DataFrame plant: table of plant data.
    :param pandas.DataFrame bus: table of bus data.
    """
    # Load data
    zip_data = get_us_zips(const.blob_paths["us_zips"])
    county_data = get_us_counties(const.blob_paths["us_counties"])

    # Determine each substation's transmission capacity, then sort for selection
    filtered_branch = branch.query("SUB_1_ID != SUB_2_ID")
    from_cap = filtered_branch.groupby("SUB_1_ID").sum()["rateA"]
    to_cap = filtered_branch.groupby("SUB_2_ID").sum()["rateA"]
    sub_cap = from_cap.combine(to_cap, lambda x, y: x + y, fill_value=0)
    # Sort substations by their capacities for later ordered selection
    sorted_subs = substations.loc[sub_cap.sort_values(ascending=False).index].copy()

    # Determine for each ZIP, how much demand to assign to each load substation
    # Assume here that generator substations don't have load attached to them
    filtered_subs = sorted_subs.loc[~sorted_subs.index.isin(plant["sub_id"])]
    subs_per_zip = filtered_subs.value_counts("ZIP")
    zip_load_substations = subs_per_zip * const.substation_load_share
    zip_load_substations = zip_load_substations.round().clip(lower=1)
    zip_assigned_population = (zip_data["population"] / zip_load_substations).dropna()
    # Select the N substations per ZIP with greatest transmission capacity
    load_substations = pd.concat(
        df.head(int(zip_load_substations[name]))
        for name, df in filtered_subs.groupby("ZIP")
    )
    substations["pop_ZIP"] = load_substations["ZIP"].map(zip_assigned_population)

    # Assign remaining county population to substations with load already,
    # plus the most connected substation in any county without a load substation.
    load_subs_from_zips = substations.query("pop_ZIP > 0")
    load_subs_per_county = load_subs_from_zips.value_counts("COUNTYFIPS")
    county_pop = county_data["population"]

    # Select the one substation per missing county with greatest transmission capacity
    counties_without_load_subs = set(county_pop.index) - set(load_subs_per_county.index)
    subs_in_counties_without_load_subs = sorted_subs.loc[
        sorted_subs["COUNTYFIPS"].isin(counties_without_load_subs)
    ]
    added_load_subs = pd.concat(
        df.head(1)
        for name, df in subs_in_counties_without_load_subs.groupby("COUNTYFIPS")
    )
    load_subs = pd.concat([load_subs_from_zips, added_load_subs])
    load_subs_per_county = load_subs_per_county.reindex(county_pop.index).fillna(1)

    # Distribute population remaining after ZIP distribution to identified load buses
    distributed_pop = load_subs.groupby("COUNTYFIPS")["pop_ZIP"].sum()
    remaining_pop = county_pop - distributed_pop.reindex(county_pop.index).fillna(0)
    remaining_pop_per_sub = remaining_pop.clip(lower=0) / load_subs_per_county
    # We may still miss some population, since there may be a county without any
    # substations, but we should cover the vast majority.
    substations["pop_county"] = load_subs["COUNTYFIPS"].map(remaining_pop_per_sub)

    # Translate population to demand
    total_pop = substations["pop_ZIP"].fillna(0) + substations["pop_county"].fillna(0)
    sub_demand = total_pop * const.demand_per_person

    load_buses = pd.concat(
        df.head(1) for sub_id, df in bus.sort_values("baseKV").groupby("sub_id")
    )
    bus["Pd"] = load_buses["sub_id"].map(sub_demand).reindex(bus.index).fillna(0)
