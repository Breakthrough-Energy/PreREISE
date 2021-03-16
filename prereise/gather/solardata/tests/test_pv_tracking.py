import pytest

from prereise.gather.solardata.pv_tracking import get_pv_tracking_ratio_state
from prereise.gather.solardata.tests.mock_pv_info import create_mock_pv_info

pv_info = create_mock_pv_info()


def test_state_type():
    state = "AZ"
    with pytest.raises(TypeError, match="state must be a list"):
        get_pv_tracking_ratio_state(pv_info, state)


def test_state_exists():
    state = ["Tatooine"]
    with pytest.raises(ValueError, match="Invalid State"):
        get_pv_tracking_ratio_state(pv_info, state)


def test_state_without_no_solar_return_none():
    state = ["MT"]
    assert get_pv_tracking_ratio_state(pv_info, state) is None


def test_state_with_solar_return_3ple():
    state = ["UT"]
    ratio = get_pv_tracking_ratio_state(pv_info, state)
    assert type(ratio) is tuple
    assert len(ratio) == 3


def test_sum_ratio_state_with_single_plant_and_tracking_system():
    state = ["UT"]
    ratio = get_pv_tracking_ratio_state(pv_info, state)
    assert sum(ratio) == 1


def test_sum_ratio_state_with_single_plant_and_multiple_tracking_systems():
    state = ["WA"]
    ratio = get_pv_tracking_ratio_state(pv_info, state)
    assert sum(ratio) == 1


def test_sum_ratio_state_with_multiple_plants_and_tracking_systems():
    state = ["CA"]
    ratio = get_pv_tracking_ratio_state(pv_info, state)
    assert sum(ratio) == 1


def test_ratio_state_with_single_plant_and_unique_tracking():
    state = ["UT"]
    ratio = get_pv_tracking_ratio_state(pv_info, state)
    assert ratio[0] == 0
    assert ratio[1] == 0
    assert ratio[2] == 1


def test_ratio_state_with_single_plant_and_multiple_tracking():
    state = ["WA"]
    ratio = get_pv_tracking_ratio_state(pv_info, state)
    assert ratio[0] == 0.5
    assert ratio[1] == 0.5
    assert ratio[2] == 0


def test_ratio_state_with_multiple_plants_and_tracking_systems():
    state = ["CA"]
    ratio = get_pv_tracking_ratio_state(pv_info, state)
    assert ratio == (1.0 / 10, 6.0 / 10, 3.0 / 10)
