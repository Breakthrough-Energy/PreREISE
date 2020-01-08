import pytest


@pytest.mark.skip(reason="Need to run on the server")
def test():
    # Moving import inside tests() so that matlab module is not a dependency.
    from prereise.call.call import launch_scenario_performance
    launch_scenario_performance('0', 16)
