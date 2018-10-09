import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import call

def test():
    call.launch_scenario_performance('western_scenarioUnitTest02', 16)
