import numpy as np
import pandas as pd
import time

import matlab.engine
eng = matlab.engine.start_matlab()


def launch_scenario_performance(scenario_name):

    scenario_list = pd.read_csv('/home/kmueller/EGMProject/ScenarioList.csv')
    # Catch if name not found
    if scenario.shape[0] == 0:
        print('No scenario with name ' + scenario_name)
        return

    scenario = scenario_list[scenario_list.name == scenario_name]

    status = eng.perform_scenario(scenario_name,
                                  scenario.load_data_location.values[0],
                                  scenario.save_data_location.values[0],
                                  scenario.start_index.values[0],
                                  scenario.end_index.values[0])
    if status == 0:
        # extract result
        print('extract result')
    else:
        # handle error
        print('error')


if __name__ == "__main__":
    import sys
    launch_scenario_performance(sys.argv[1])
