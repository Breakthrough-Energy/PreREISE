import pytest

from prereise.gather.demanddata.bldg_electrification import const
from prereise.gather.demanddata.bldg_electrification.ff2elec_profile_generator_htg import (
    generate_htg_profiles,
)


def test_generate_profiles_argument_type():
    args = (
        ("2016", const.state_list, "res", "advperfhp"),
        (2016, const.state_list, 3, "advperfhp"),
        (2016, const.state_list, "com", 3),
    )
    for a in args:
        with pytest.raises(TypeError):
            generate_htg_profiles(a[0], a[1], a[2], a[3])
