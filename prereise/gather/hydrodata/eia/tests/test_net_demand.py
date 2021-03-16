import pandas as pd
import pytest
from powersimdata.tests.mock_scenario import MockScenario

from prereise.gather.hydrodata.eia.net_demand import get_net_demand_profile

mock_plant = {
    "plant_id": ["1001", "1002", "1003"],
    "zone_name": ["Bay Area", "Central California", "Washington"],
    "type": ["solar", "wind", "hydro"],
}

grid_attrs = {"plant": mock_plant}

mock_wind = pd.DataFrame({"1002": [1, 1, 1, 1]})

mock_solar = pd.DataFrame({"1001": [2, 2, 2, 2]})

mock_demand = pd.DataFrame(
    {
        101: [1, 2, 3, 4],
        102: [4, 3, 2, 1],
        103: [2, 2, 2, 2],
    }
)

scenario = MockScenario(
    grid_attrs, demand=mock_demand, wind=mock_wind, solar=mock_solar
)
scenario.state.grid.zone2id = {
    "Bay Area": 101,
    "Central California": 102,
    "Washington": 103,
}


def test_get_net_demand_profile_argument_type():
    arg = ((1, scenario, None), ("CA", 1, None), ("WA", None, 1))
    for a in arg:
        with pytest.raises(TypeError):
            get_net_demand_profile(a[0], scenario=a[1], interconnect=a[2])


def test_get_net_demand_profile_argument_value():
    scenario_create = MockScenario()
    scenario_create.state = "Create"
    arg = (
        ("Spain", scenario, None),
        ("WA", scenario_create, None),
        ("CA", None, None),
    )
    for a in arg:
        with pytest.raises(ValueError):
            get_net_demand_profile(a[0], a[1], a[2])


def test_get_net_demand_profile():
    expected = pd.Series(
        [2, 2, 2, 2],
        index=pd.date_range(
            start="2016-01-01 00:00:00", end="2016-01-01 03:00:00", freq="H"
        ),
    )
    assert expected.equals(get_net_demand_profile("CA", scenario))
