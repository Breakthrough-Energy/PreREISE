from prereise.gather.griddata.hifld import const


def map_state_and_county_to_interconnect(state_abv, county):
    """Map a state and a county to an assumed interconnection.

    :param str state_abv: two-letter state abbreviation.
    :param str county: county name.
    :raises ValueError: if the provided state abbreviation isn't present in mappings.
    :return: (*str*) -- interconnection name.
    """
    state_upper = state_abv.upper()
    for region in ("Eastern", "Western"):
        if state_upper in const.interconnect2state[region]:
            return region
    if state_upper in const.interconnect2state["split"]:
        for region in set(const.state_county_splits[state_upper].keys()) - {"default"}:
            if county.upper() in const.state_county_splits[state_upper][region]:
                return region
        return const.state_county_splits[state_upper]["default"]
    raise ValueError(f"Got an unexpected state: {state_abv}")
