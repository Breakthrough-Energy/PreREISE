import datetime

import pytest

from prereise.gather.winddata.rap.noaa_api import NoaaApi


@pytest.fixture
def noaa():
    box = {"north": 49.8203, "south": 25.3307, "west": -122.855, "east": -96.2967}
    return NoaaApi(box)


start_date = "2018-03-05"
end_date = "2018-03-06"
start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
end = datetime.datetime.strptime(end_date, "%Y-%m-%d")


def test_get_url_list(noaa):
    urls = noaa.get_path_list(start, end)
    first = "201803/20180305/rap_130_20180305_0000_000.grb2"
    last = "201803/20180306/rap_130_20180306_2300_000.grb2"
    assert first == urls[0]
    assert last == urls[-1]


def test_box_query_set(noaa):
    keys = [k[0] for k in noaa.params]
    for a in ["north", "south", "east", "west"]:
        assert a in keys


def test_url_fallback_default(noaa):
    url = noaa.build_url("month/day/filename")
    fallback = noaa.build_url("month/day/filename", fallback=True)
    assert "old" not in url
    assert "old" in fallback


def test_box_validation():
    for a in (None, [], "box", ("north", 4)):
        with pytest.raises(TypeError):
            NoaaApi(a)

    wrong = {"foo": 5, "west": "whatever"}
    missing = {"north": 49.8203, "west": -122.855, "east": -96.2967}
    for a in (wrong, missing):
        with pytest.raises(ValueError):
            NoaaApi(a)
