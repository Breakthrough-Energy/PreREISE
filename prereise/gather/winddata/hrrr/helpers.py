from prereise.gather.winddata.hrrr.constants import (
    DEFAULT_HOURS_FORECASTED,
    DEFAULT_PRODUCT,
)


def formatted_filename(
    dt, product=DEFAULT_PRODUCT, hours_forecasted=DEFAULT_HOURS_FORECASTED
):
    """Deterministically returns a grib filename

    :param datetime.datetime dt: datetime associated with
        the data being stored
    :param string product: product associated with the
        data being stored
    :param string hours_forecasted: how many hours into
        the future the data is forecasted

    :return: (*str*) -- a filename
    """
    return f"{dt.strftime('%Y_%m_%d_%Hhr')}_{product}_{hours_forecasted}.grib2"


def get_indices_that_contain_selector(input_list, selectors):
    """Generates list of indices of strings in input_list that
    contain a string inside of selectors

    :param list input_list: list of strings
    :param list selectors: list of strings

    :return: (*list*) -- list of indices of strings in input_list
        that contain a string inside of selectors
    """
    return [
        i
        for i, item in enumerate(input_list)
        if any([selector in item for selector in selectors])
    ]
