import os
import sys
import unittest

import pytest

from prereise.call.call import launch_scenario_performance


@pytest.mark.skip(reason="Need to run on the server")
def test():
    launch_scenario_performance('western_scenarioUnitTest02', 16)
