import re

import pandas as pd
import requests
from tqdm import tqdm

from prereise.gather.impute import linear

category_template = (
    "https://api.eia.gov/category/?api_key={api_key}&category_id={category_id}"
)
series_template = "https://api.eia.gov/series/?api_key={api_key}&series_id={series_id}"
top_level_category_id = 3390101


def parse_input_regions(available_regions, requested_regions):
    """Parse requested regions, allowing either exact string matches or balancing
    authority abbreviations.

    :param iterable available_regions: set of available regions (str).
    :param iterable requested_regions: set of request regions (str).
    :return: (*set*) -- parsed regions.
    :raises ValueError: if any requested region isn't present in the set available from
        EIA, or matches multiple available regions.
    """
    parsed_regions = set()
    for r in requested_regions:
        if r in available_regions:
            parsed_regions.add(r)
            continue
        abbreviation_matches = {a for a in available_regions if f"({r})" in a}
        if len(abbreviation_matches) == 0:
            print(f"No hydro data available for region {r}, skipping")
            continue
        if len(abbreviation_matches) > 1:
            raise ValueError(f"Multiple regions found for {r}: {abbreviation_matches}")
        (single_match,) = abbreviation_matches  # unpack singleton set
        parsed_regions.add(single_match)
    return parsed_regions


def get_generation(api_key, year, regions=None, acceptable_missing=48, verbose=False):
    """Fetch hourly generation by balancing authority from EIA, filter to regions with
    a full year of hydro data for the given year.

    :param str api_key: EIA api key from <https://www.eia.gov/opendata/register.php>.
    :param int/str year: year of data to return. Any regions with too many missing
        entries in this year will be dropped (see ``acceptable_missing``).
    :param iterable regions: subset of regions to fetch & return. If None, all will be
        returned.
    :param int acceptable_missing: the maximum allowable number of missing hours of data
        for each region. If an allowable number of hours are missing, values will be
        linearly imputed. If more than this number are missing in the given ``year``,
        the region will be dropped from the output.
    :param bool verbose: whether or not to report the number of missing hours for each
        region which gets dropped (based on the ``acceptable_missing`` parameter).
    :return: (*pandas.DataFrame*) -- index is hourly timestamps in the given year,
        columns are balancing authority abbreviations, values are total hydro generation
        (MW).
    """
    # This request gives us the available subcategories (regions)
    regions_metadata = requests.get(
        category_template.format(api_key=api_key, category_id=top_level_category_id)
    ).json()
    region_categories = {
        c["name"]: c["category_id"]
        for c in regions_metadata["category"]["childcategories"]
    }
    available_regions = region_categories.keys()
    if regions is None:
        regions = region_categories.keys()
    parsed_regions = parse_input_regions(available_regions, regions)
    parsed_series_data = []
    skipped_regions = set()
    for region in tqdm(parsed_regions, total=len(parsed_regions)):
        # This request gives us the available sub-sub-categories (fuel, timezone)
        url = category_template.format(
            api_key=api_key, category_id=region_categories[region]
        )
        subcategories_response = requests.get(url).json()
        # Filter these by their names to hydro, UTC
        matching_series_set = {
            series["series_id"]
            for series in subcategories_response["category"]["childseries"]
            if "hourly - UTC time" in series["name"] and "hydro" in series["name"]
        }
        # Check for existence of UTC hydro data
        if len(matching_series_set) == 0:
            skipped_regions.add(region)
            continue
        # Extract the only value from a singleton set
        (series_id,) = matching_series_set
        # Query just that series
        series_response = requests.get(
            series_template.format(api_key=api_key, series_id=series_id)
        ).json()
        # Parse the full response to a Series containing just the data
        series_data = (
            pd.DataFrame(series_response["series"][0]["data"]).set_index(0).squeeze()
        )
        series_data.index = pd.to_datetime(series_data.index)
        series_data.name = region
        parsed_series_data.append(series_data)
    if len(skipped_regions) > 0:
        print(f"no hydro data found for {sorted(skipped_regions)}")
    full_data = pd.concat(parsed_series_data, axis=1)
    # Evaluate the number of missing entries for each region
    num_missing = full_data.loc[f"{year}-01-01-00":f"{year}-12-31-23"].isna().sum()
    acceptable_num_missing = num_missing <= acceptable_missing
    imputed_regions = full_data.columns[
        (0 < num_missing) & (num_missing <= acceptable_missing)
    ]
    missing_entry_regions = full_data.columns[~acceptable_num_missing]
    full_year_data_regions = full_data.columns[acceptable_num_missing]
    if len(imputed_regions) > 0:
        print(f"acceptable missing entries for {sorted(imputed_regions)}, imputing")
    if len(missing_entry_regions) > 0:
        print(f"inadequate data for {sorted(missing_entry_regions)} for {year}")
    if verbose and len(missing_entry_regions) > 0:
        print(num_missing.loc[missing_entry_regions])
    # Impute
    imputed = linear(
        full_data.loc[f"{year}-01-01-00":f"{year}-12-31-23", full_year_data_regions],
        inplace=False,
    )
    # Rename columns for brevity. 'Longname (ABV)' becomes simply 'ABV'
    imputed.columns = [
        re.search(r"\(([A-Z]*[0-9]*)\)", c).group(1) for c in imputed.columns
    ]
    return imputed
