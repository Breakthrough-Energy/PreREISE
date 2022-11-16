from prereise.gather.demanddata.transportation_electrification.dwelling import (
    get_energy_limit,
    get_segment,
)


def test_get_segment():
    segments = get_segment(2.3, 5.5)

    assert segments == 6


def test_energy_limit():
    energy_limit = get_energy_limit(10, 6, 3.3, 6.2, 0.5)

    assert energy_limit == [3.500000000000001, 5.0, 5.0, 5.0, 5.0, 2.5]
