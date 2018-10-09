import os
import sys
import unittest

import call

sys.path.insert(0,
                os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test():
    call.launch_scenario_performance('western_scenarioUnitTest02', 16)
