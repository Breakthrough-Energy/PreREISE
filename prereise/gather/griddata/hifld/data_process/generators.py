import pandas as pd
from powersimdata.utility.distance import haversine
from scipy.optimize import curve_fit
from scipy.stats import linregress

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
        lambda x: haversine((x.lat, x.lon), (generator.lat, generator.lon)),
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


def estimate_heat_rate_curve(
    generator, epa_ampd_groupby, crosswalk_translation, min_unique_x=3, min_points=24
):
    """Estimate a generator's heat rate curve if data are present in the EPA AMPD data,
    otherwise return NA.

    :param pandas.Series generator: one generating unit from data frame.
    :param pandas.GroupBy epa_ampd_groupby: data frame of EPA AMPD samples, grouped by
        plant ID and unit ID.
    :param pandas.Series crosswalk_translation: mapping of EIA keys to EPA keys.
    :param int min_unique_x: minimum number of unique x points needed to fit a curve to.
    :param int min_points: minimum number points needed to fit a curve to.
    :return: (*tuple*) -- if possible, quadratic coefficients:
        h0 (constant), h1 (linear), and h2 (quadratic); respectively. Otherwise, return
        NA values for each
    """

    def quadratic(x, a, b, c):
        return a + b * x + c * x**2

    quadratic_coefficient_bounds = ([0] * 3, [float("inf")] * 3)
    return_index = ["h0", "h1", "h2"]
    default_return = pd.Series([float("nan")] * 3, index=return_index)
    eia_key = (generator["Plant Code"], generator["Generator ID"])
    x_col = "GLOAD (MW)"
    y_col = "HEAT_INPUT (mmBtu)"
    try:
        epa_key = crosswalk_translation.loc[eia_key].values[0]
        samples = epa_ampd_groupby.get_group(epa_key)
        filtered_samples = samples.loc[
            (samples[x_col] != 0)
            & (samples[y_col] != 0)
            & ~samples[x_col].isnull()
            & ~samples[y_col].isnull()
        ]
        if len(filtered_samples[x_col].unique()) < min_unique_x:
            return default_return
        if len(filtered_samples) < min_points:
            return default_return
        xs = filtered_samples[x_col]
        ys = filtered_samples[y_col]
        popt, _ = curve_fit(quadratic, xs, ys, bounds=quadratic_coefficient_bounds)
        return pd.Series(popt, index=return_index)
    except KeyError:
        return default_return


def filter_suspicious_heat_rates(generators):
    """Identify linearized heat rates which violate assumptions of 'reasonable' bounds,
    and replace them with NaN values.

    :param pandas.DataFrame generators: data frame of generators with fitted heat rates
        (modified inplace).
    """

    def get_heat_rate_bounds(generator):
        """Lookup heat rate bounds for a generator, by either type or type and capacity.

        :param pandas.Series generator: single generator attributes.
        :return: (*pandas.Series*) -- heat rate bounds ('lower', 'upper').
        """
        gen_type = tuple(generator[["Technology", "Prime Mover"]])
        if gen_type in const.reasonable_heat_rates_by_type:
            data = const.reasonable_heat_rates_by_type[gen_type]
        key = (
            gen_type + ("small",)
            if generator["Pmax"]
            < const.reasonable_heat_rates_size_cutoffs.get(gen_type, 0)
            else gen_type + ("large",)
        )
        data = const.reasonable_heat_rates_by_type_and_size.get(key, (0, float("inf")))
        return pd.Series(data, index=("lower", "upper"))

    heat_rate_bound_types = set(const.reasonable_heat_rates_size_cutoffs.keys()) | set(
        const.reasonable_heat_rates_by_type.keys()
    )
    generator_types = generators[["Technology", "Prime Mover"]].apply(tuple, axis=1)
    gens_with_coefficients = generators.loc[
        generator_types.isin(heat_rate_bound_types) & ~generators["h0"].isna()
    ]
    # Simplified calculation for rise/run for quadratic curve evaluated at Pmin and Pmax
    single_segment_slope = (
        gens_with_coefficients["h2"]
        * (gens_with_coefficients["Pmax"] + gens_with_coefficients["Pmin"])
        + gens_with_coefficients["h1"]
    )
    heat_rate_bounds = gens_with_coefficients.apply(get_heat_rate_bounds, axis=1)
    good_heat_rates = single_segment_slope.loc[
        (heat_rate_bounds["lower"] <= single_segment_slope)
        & (single_segment_slope <= heat_rate_bounds["upper"])
    ]
    generators.loc[
        ~generators.index.isin(good_heat_rates.index), ["h0", "h1", "h2"]
    ] = float("nan")


def augment_missing_heat_rates(generators):
    """Identify generators with NaN heat rate coefficients, replace with quadratic
    coefficients from a linear regression against other generators of that type (for
    fossil generators) or with assumed linear coefficients for non-fossil generators.

    :param pandas.DataFrame generators: data frame of generators with fitted heat rates
        (modified inplace).
    """

    def estimate_coefficients(generator, regressions):
        """Estimate heat rate coefficients for a generator, by type and capacity.

        :param pandas.Series generator: single generator attributes.
        :param dict regressions: nested dictionary of fitted regressions:
            first level is ('Technology', 'Prime Mover') attributes,
            second level is {'h0', 'h1', 'h2'}, values are regressions against Pmax.
        :return: (*pandas.Series*) -- heat rate parameters: (h0, h1, h2).
        """
        regression_key = tuple(generator[["Technology", "Prime Mover"]])
        if regression_key not in regressions:
            return pd.Series([float("nan")] * 3, index=["h0", "h1", "h2"])
        type_regressions = regressions[regression_key]
        estimates = pd.Series(
            {
                coef: (regression.intercept + regression.slope * generator["Pmax"])
                for coef, regression in type_regressions.items()
            },
        )
        return estimates

    output_index = ["h0", "h1", "h2"]

    # Augment heat rate for fossil generators
    gens_with_coefficients = generators.loc[~generators["h0"].isnull()]
    gen_groups = gens_with_coefficients.groupby(["Technology", "Prime Mover"])
    regressions = {
        technology: {
            coef: linregress(group["Pmax"], group[coef]) for coef in output_index
        }
        for technology, group in gen_groups
    }
    gens_without_coefficients = generators.loc[generators["h0"].isnull()]
    filled_coefficients = gens_without_coefficients.apply(
        lambda x: (estimate_coefficients(x, regressions)), axis=1
    )
    generators.update(filled_coefficients)

    # Augment heat rates for non-fossil generators
    linear_heat_rate_assumptions = (
        generators["Technology"]
        .map(const.heat_rate_assumptions)
        .to_frame(name="h1")
        .apply(
            lambda x: (
                pd.Series([float("nan")] * 3, index=output_index)
                if pd.isna(x["h1"])
                else pd.Series([0, x["h1"], 0], index=output_index)
            ),
            axis=1,
        )
    )
    generators.update(linear_heat_rate_assumptions)


def build_plant(bus, substations, kwargs={}):
    """Use source data on generating units from EIA/EPA, along with transmission network
    data, to produce a plant data frame.

    :param pandas.DataFrame bus: data frame of buses, to be used within
        :func:`map_generator_to_bus_by_sub`.
    :param pandas.DataFrame substations: data frame of substations.
    :param dict kwargs: keyword arguments to be passed to lower level-functions,
        i.e. :func:`estimate_heat_rate_curve`.
    :return: (*pandas.DataFrame*) -- data frame of generator data.
    """
    # Initial loading
    generators = load.get_eia_form_860(const.blob_paths["eia_form860_2019_generator"])
    plants = load.get_eia_form_860(const.blob_paths["eia_form860_2019_plant"])
    print("Fetching EPA data... (this may take several minutes)")
    epa_ampd = load.get_epa_ampd(const.blob_paths["epa_ampd"])
    crosswalk = load.get_eia_epa_crosswalk(const.eia_epa_crosswalk_path)

    # Data interpretation
    plants = plants.set_index("Plant Code")
    plants["Latitude"] = plants["Latitude"].map(floatify)
    plants["Longitude"] = plants["Longitude"].map(floatify)
    for col in ["Summer Capacity (MW)", "Winter Capacity (MW)", "Minimum Load (MW)"]:
        generators[col] = generators[col].map(floatify)
    crosswalk_translation = (
        crosswalk.set_index(["MOD_EIA_PLANT_ID", "MOD_CAMD_GENERATOR_ID"])
        .apply(
            lambda x: (x["CAMD_PLANT_ID"], x["MOD_CAMD_UNIT_ID"]),
            axis=1,
        )
        .sort_index()
    )

    # Filtering / Grouping
    generators = generators.query(
        "Technology not in @const.eia_storage_gen_types"
    ).copy()
    bus_groupby = bus.groupby(bus["sub_id"].astype(int))
    # Filter substations with no buses
    substations = substations.loc[set(bus_groupby.groups.keys())]
    substation_groupby = substations.groupby(["interconnect", "ZIP"])
    epa_ampd_groupby = epa_ampd.groupby(["ORISPL_CODE", "UNITID"])

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
    # Drop generators with no capacity listed
    generators = generators.loc[~generators["Pmax"].isnull()]
    generators.rename({"Minimum Load (MW)": "Pmin"}, inplace=True, axis=1)
    generators["Pmin"] = generators["Pmin"].fillna(0)
    print("Fitting heat rate curves to EPA data... (this may take several minutes)")
    heat_rate_curve_estimates = generators.apply(
        lambda x: estimate_heat_rate_curve(
            x, epa_ampd_groupby, crosswalk_translation, **kwargs
        ),
        axis=1,
    )
    generators = generators.join(heat_rate_curve_estimates)
    filter_suspicious_heat_rates(generators)
    augment_missing_heat_rates(generators)
    # Drop generators whose heat rates can't be estimated
    to_be_dropped = generators.loc[generators["h1"].isnull()]
    print(
        f"Dropping generators whose heat rates can't be estimated: {len(to_be_dropped)}"
        f" out of {len(generators)}, {round(to_be_dropped['Pmax'].sum(), 0)} MW out of "
        f"{round(generators['Pmax'].sum(), 0)} total MW"
    )
    print(to_be_dropped.groupby(["Technology", "Prime Mover"])["Pmax"].sum())
    generators.drop(to_be_dropped.index, inplace=True)
    # Add fuel costs, calculate cost curves from heat rate curves
    generators["GenFuelCost"] = generators["Energy Source 1"].map(const.fuel_prices)
    for i in range(3):
        generators[f"c{i}"] = generators[f"h{i}"] * generators["GenFuelCost"].fillna(0)

    generators = generators.loc[~generators["bus_id"].isna()].copy()
    # Rename columns (or add as necessary) to match PowerSimData expectations
    generators.rename(
        {"Energy Source 1": "type", "h1": "GenIOB", "h2": "GenIOC"},
        axis=1,
        inplace=True,
    )
    generators["type"] = generators["type"].replace(const.fuel_translations)
    generators["GenIOD"] = 0
    generators.index.name = "plant_id"

    return generators
