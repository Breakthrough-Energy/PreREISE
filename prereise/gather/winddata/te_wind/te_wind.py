import math

import numpy as np
import pandas as pd
from bokeh.sampledata.us_states import data as states

from pywtk.site_lookup import get_3tiersites_from_wkt
from pywtk.wtk_api import get_nc_data_from_url
from tqdm import tqdm


def _great_circle_distance(lat1, lon1, lat2, lon2):
    """Calculates distance between two sites

    :param float lat1: latitude of first site (in rad.)
    :param float lon1: longitude of first site (in rad.)
    :param float lat2: latitude of second site (in rad.)
    :param float lon2: longitude of second site (in rad.)
    :return: (*float*) -- distance between two sites (in km.).
    """
    radius = 6368

    def haversine(x):
        return math.sin(x / 2) ** 2

    return (
        radius
        * 2
        * math.asin(
            math.sqrt(
                haversine(lat2 - lat1)
                + math.cos(lat1) * math.cos(lat2) * haversine(lon2 - lon1)
            )
        )
    )


def get_nrel_site(state):
    """Retrieve ID of wind farms in given state.

    :param list state: list of state abbreviation.
    :return: (*pandas.DataFrame*) -- data frame with *'site_id'*, *'lat'*,
        *'lon'*, *'capacity'* and *'capacity_factor'* as columns.
    """
    site = None

    for s in state:
        coord = np.column_stack((states[s]["lons"], states[s]["lats"]))

        # Prepare coordinates for call
        # Convert into string format
        out_tot = []
        for i in coord:
            out = str(i[0]) + " " + str(i[1]) + ","
            out_tot.append(out)
        out = str(coord[0][0]) + " " + str(coord[0][1])
        out_tot.append(out)
        str1 = "".join(out_tot)
        str_final = "POLYGON((" + str1 + "))"
        print("Retrieving nrel sites for " + s)
        site_tmp = get_3tiersites_from_wkt(str_final)
        print("Got " + str(site_tmp.shape[0]) + " sites in " + s)
        site_tmp = site_tmp.reset_index()
        if site is not None:
            site = site.append(
                site_tmp[["site_id", "lat", "lon", "capacity", "capacity_factor"]]
            )
        else:
            site = site_tmp[
                ["site_id", "lat", "lon", "capacity", "capacity_factor"]
            ].copy()
    return site


def site2farm(site, wind_farm):
    """Find NREL site closest to wind farm.

    :param pandas.DataFrame site: data frame with *'site_id'*, *'lat'*,
        *'lon'* and *'capacity'* as columns. Same structure as the one returned
        by :func:`get_nrel_site`.
    :param pandas.DataFrame wind_farm: data frame with *'lat'*, *'lon'* as
        columns and *'plant_id'* as indices. The order of the columns is
        important.
    :return: (*pandas.DataFrame*) -- data frame with *'site_id'*, '*capacity*'
        and *'dist'* as columns and *'plant_id'* as indices.
    """
    closest_site = pd.DataFrame(
        index=wind_farm.index, columns=["site_id", "capacity", "dist"]
    )
    # Iterate trough wind farms and find closest NREL site
    for i, row in enumerate(tqdm(wind_farm.itertuples(), total=wind_farm.shape[0])):
        dist = site.apply(
            lambda row_site: _great_circle_distance(
                row_site["lat"], row_site["lon"], row[1], row[2]
            ),
            axis=1,
        )
        closest_site.iloc[i].dist = dist.min()
        closest_site.iloc[i].site_id = site["site_id"][dist == dist.min()].values[0]
        closest_site.iloc[i].capacity = site["capacity"][dist == dist.min()].values[0]
    closest_site.index.name = "plant_id"
    closest_site.site_id = closest_site.site_id.astype(int)
    closest_site.capacity = closest_site.capacity.astype(float)
    closest_site.dist = closest_site.dist.astype(float)
    return closest_site


def get_data(site, date_range):
    """Get power and wind speed data from NREL server.

    :param pandas.DataFrame site: data frame with *'site_id'* and '*capacity*'
        as columns. Same structure as the one returned by :func:`site2farm`.
    :param pandas.date_range date_range: date_range, freq needs to be 5 min.
    :return: (*dict*) -- dictionary of data frame with *'power'* and
        *'wind_speed'* as columns and timestamp as indices. The data is
        normalized using the capacity of the plant. The first key is a
        month-like timestamp (e.g. *'2010-10'*). The second key is the site id
        number (e.g. *'121409'*). Then, site_dict['2012-12'][121409] is a data
        frame.
    """

    wtk_url = "https://f9g6p4cbvi.execute-api.us-west-2.amazonaws.com/prod"

    # Retrieving data from NREL server
    utc = True
    leap_day = True
    # We use a dict because the output is a tensor
    # 1: site
    # 2: date(month)
    # 3: attribute(power, wind_speed)
    data = {}
    # Use helper DataFrame to specify download interval
    helper = pd.DataFrame(index=date_range)

    for y in tqdm(helper.index.year.unique()):
        for m in tqdm(helper[str(y)].index.month.unique(), desc=str(y)):
            if m < 10:
                month = str(y) + "-0" + str(m)
            else:
                month = str(y) + "-" + str(m)
            data[month] = {}
            start = helper[month].index[0]
            end = helper[month].index[-1]
            attributes = ["power", "wind_speed"]

            for row in tqdm(
                site.drop_duplicates(subset="site_id").itertuples(),
                desc=month,
                total=len(site.drop_duplicates(subset="site_id")),
            ):
                site_id = row[1]
                capacity = row[2]
                tqdm.write("Call " + str(site_id) + " " + str(start) + " " + str(end))
                data[month][site_id] = (
                    get_nc_data_from_url(
                        wtk_url + "/met",
                        site_id,
                        start,
                        end,
                        attributes,
                        utc=utc,
                        leap_day=leap_day,
                    )
                    / capacity
                )
    print("Done retrieving data from NREL server")
    return data


def dict2frame(data, date_range, closest_site):
    """Converts dictionary into two data frames. One is power, the other is wind
        speed.

    :param dict data: dictionary of data frame with *'power'* and *'wind_speed'*
        as columns and timestamp as indices. The first key is a month-like
        timestamp (e.g. *'2010-10'*). The second key is the site id number (e.g.
        *'121409'*). It is returned by :func:`get_data`.
    :param pandas.date_range date_range: date range for the data.
    :param pandas.DataFrame closest_site: data frame with *'site_id'* as
        column and *'plant_id'* as indices.
    :return: (*list*) -- Two data frames, one for power and one for wind speed.
        Column is *'site_id'* and indices are timestamp.
    """
    power = pd.DataFrame(
        index=date_range, columns=closest_site["site_id"].drop_duplicates(), dtype=float
    )
    wsp = pd.DataFrame(
        index=date_range, columns=closest_site["site_id"].drop_duplicates(), dtype=float
    )

    for month in data:
        print(month)
        for site_id in tqdm(data[month]):
            power.loc[month, site_id] = data[month][site_id]["power"].values
            wsp.loc[month, site_id] = data[month][site_id]["wind_speed"].values
    return [power, wsp]


def get_profile(power, wind_farm, closest_site):
    """Scales power to plant capacity.

    :param pandas.DataFrame power: data frame with *'site_id'* as columns
        and timestamp as indices. Same structure as the one returned by
        :func:`dict2frame`.
    :param pandas.DataFrame wind_farm: data frame with *'Pmax'* as
        column and *'plant_id'* as indices.
    :param pandas.DataFrame closest_site: data frame with *'site_id'*,
        '*capacity*' and *'dist'* as columns and *'plant_id'* as indices. It is
        returned by :func`site2farm`.
    :return: (*pandas.DataFrame*) -- data frame of the power generated with
        *'plant_id'* as columns and timestamp as indices.
    """
    profile = pd.DataFrame(index=power.index, columns=wind_farm.index.values)
    for plant_id, Pmax in wind_farm["Pmax"].iteritems():
        site_id = closest_site.loc[plant_id, "site_id"]
        profile[plant_id] = power[site_id] * Pmax

    return profile.resample("H").mean()
