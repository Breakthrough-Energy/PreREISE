import pytest

from prereise.gather.helpers import get_monthly_net_generation
from prereise.gather.tests.mock_generation import create_mock_generation_data_frame


def test_get_monthly_net_generation_argument_type():
    arg = (
        (1, create_mock_generation_data_frame(), "hydro"),
        ("CA", 1, "hydro"),
        ("WA", create_mock_generation_data_frame(), 1),
    )
    for a in arg:
        with pytest.raises(TypeError):
            get_monthly_net_generation(a[0], a[1], a[2])


def test_get_monthly_net_generation_argument_value():
    arg = (
        ("Germany", create_mock_generation_data_frame(), "hydro"),
        ("WA", create_mock_generation_data_frame(), "uranium"),
    )
    for a in arg:
        with pytest.raises(ValueError):
            get_monthly_net_generation(a[0], a[1], a[2])


def test_get_monthly_net_generation():
    table = create_mock_generation_data_frame()
    state = "CA"
    fuel_types = [
        "wind",
        "solar",
        "ng",
        "dfo",
        "hydro",
        "geothermal",
        "nuclear",
        "coal",
    ]
    res = [
        get_monthly_net_generation(state, table, fuel_type) for fuel_type in fuel_types
    ]

    for i in range(8):
        assert res[i] == [i + 1] * 12
