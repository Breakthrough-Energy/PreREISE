from dataclasses import dataclass
from datetime import timedelta

import pandas as pd

from prereise.gather.request_util import RateLimit, retry


@dataclass
class Psm3Data:
    """Wrapper class for PSM3 data retrieved from NREL's API. Contains metadata
    from the first csv row and a data frame representing the remaining time series
    """

    lat: float
    lon: float
    tz: float
    elevation: float
    data_resource: pd.DataFrame

    allowed_attrs = {
        "dni": "DNI",
        "dhi": "DHI",
        "wind_speed": "Wind Speed",
        "air_temperature": "Temperature",
        "ghi": "GHI",
    }

    rename_attrs = {
        "DHI": "df",
        "DNI": "dn",
        "Wind Speed": "wspd",
        "Temperature": "tdry",
    }

    @staticmethod
    def check_attrs(attributes):
        for a in attributes.split(","):
            if a not in Psm3Data.allowed_attrs.keys():
                raise ValueError(f"Unsupported attribute: {a}")

    def to_dict(self):
        """Convert the data to the format expected by nrel-pysam for running
        SAM simulations

        :return: (*dict*) -- a dictionary which can be passed to the pvwattsv7
        module
        """
        result = {
            "lat": self.lat,
            "lon": self.lon,
            "tz": self.tz,
            "elev": self.elevation,
            "year": self.data_resource.index.year.tolist(),
            "month": self.data_resource.index.month.tolist(),
            "day": self.data_resource.index.day.tolist(),
            "hour": self.data_resource.index.hour.tolist(),
            "minute": self.data_resource.index.minute.tolist(),
        }
        result.update(
            {
                Psm3Data.rename_attrs[v]: self.data_resource[v].tolist()
                for v in Psm3Data.allowed_attrs.values()
                if v in self.data_resource.columns
            }
        )
        return result


class NrelApi:
    """Provides an interface to the NREL API for PSM3 data. It supports
    downloading this data in csv format, which we use to calculate solar output
    of a set of plants. The user will need to provide an API key.
    :param str email: email used for API key
        `sign up <https://developer.nrel.gov/signup/>`_.
    :param str api_key: API key.
    :param int/float rate_limit: minimum seconds to wait between requests to NREL
    """

    def __init__(self, email, api_key, rate_limit=None):
        """Constructor"""
        if email is None:
            raise ValueError("Email is required")
        if api_key is None:
            raise ValueError("API key is required")

        self.email = email
        self.api_key = api_key
        self.interval = rate_limit

    def _build_url(self, lat, lon, attributes, year="2016", leap_day=False):
        """Construct url with formatted query string for downloading psm3
        (physical solar model) data

        :param str lat: latitude of the plant
        :param str lon: longitude of the plant
        :param str attributes: comma separated list of attributes to query
        :param str year: the year
        :param bool leap_day: whether to use a leap day
        :return: (*str*) -- the url to download csv data
        """
        base_url = "https://developer.nrel.gov/api/solar/nsrdb_psm3_download.csv"
        payload = {
            "api_key": self.api_key,
            "names": year,
            "leap_day": str(leap_day).lower(),
            "interval": "60",
            "utc": "true",
            "email": self.email,
            "attributes": attributes,
            "wkt": f"POINT({lon}%20{lat})",
        }
        query = "&".join([f"{key}={value}" for key, value in payload.items()])
        return f"{base_url}?{query}"

    def get_psm3_at(self, lat, lon, attributes, year, leap_day, dates=None):
        """Get PSM3 data at a given point for the specified year.

        :param str lat: latitude of the plant
        :param str lon: longitude of the plant
        :param str attributes: comma separated list of attributes to query
        :param str year: the year
        :param bool leap_day: whether to use a leap day
        :param pd.DatetimeIndex dates: if provided, use to index the downloaded data frame

        :return: (*prereise.gather.solardata.nsrdb.nrel_api.Psm3Data*) -- a data class containing metadata and time series for the given year and location
        """
        Psm3Data.check_attrs(attributes)
        url = self._build_url(lat, lon, attributes, year, leap_day)

        @retry(interval=self.interval)
        def _get_info(url):
            return pd.read_csv(url, nrows=1)

        @retry(interval=self.interval)
        def _get_data(url):
            return pd.read_csv(url, dtype=float, skiprows=2)

        info = _get_info(url)
        tz, elevation = info["Local Time Zone"], info["Elevation"]

        data_resource = _get_data(url)

        if dates is not None:
            data_resource.set_index(
                dates + timedelta(hours=int(tz.values[0])), inplace=True
            )
        return Psm3Data(
            float(lat), float(lon), float(tz), float(elevation), data_resource
        )
