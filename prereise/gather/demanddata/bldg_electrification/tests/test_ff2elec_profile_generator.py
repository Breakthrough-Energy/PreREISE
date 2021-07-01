import pytest

from prereise.gather.demanddata.bldg_electrification.ff2elec_profile_generator import (
    generate_profiles,
)


def test_generate_profiles_argument_type():
    args = (("2016", "res", "advperfhp"), (2016, 3, "advperfhp"), (2016, "com", 3))
    for a in args:
        with pytest.raises(TypeError):
            generate_profiles(a[0], a[1], a[2])
