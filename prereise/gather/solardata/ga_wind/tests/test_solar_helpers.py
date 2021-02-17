from pyproj import Transformer

from prereise.gather.solardata.ga_wind.helpers import ll2ij, proj_string


def test_ll2ij():
    transformer = Transformer.from_pipeline(proj_string)
    # Seattle
    assert ll2ij(transformer, 123.30661, 19.624062, -122.33, 47.61) == (-3568, 3435)
    # Washington DC
    assert ll2ij(transformer, 123.30661, 19.624062, -77.01, 38.91) == (-4097, 5162)
