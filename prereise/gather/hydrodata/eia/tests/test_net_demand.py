import pandas as pd
import pytest
from powersimdata.tests.mock_scenario import MockScenario

from prereise.gather.hydrodata.eia.net_demand import get_net_demand_profile

scenario_analyze = MockScenario()


def test_get_net_demand_profile_argument_type():
    arg = ((1, scenario_analyze), ("CA", 1))
    for a in arg:
        with pytest.raises(TypeError):
            get_net_demand_profile(a[0], a[1])


def test_get_net_demand_profile_argument_value():
    scenario_create = MockScenario()
    scenario_create.state = "Create"
    arg = (("Spain", scenario_analyze), ("WA", scenario_create))
    for a in arg:
        with pytest.raises(ValueError):
            get_net_demand_profile(a[0], a[1])
