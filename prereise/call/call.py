import numpy as np
import pandas as pd
import time
import os

import matlab.engine
eng = matlab.engine.start_matlab()


def launch_scenario_performance(scenario_name):
    # Load scenario list
    top_dirname = os.path.dirname(__file__)
    top_dirname = os.path.join(top_dirname, '../')
    scenario_dirname = '/home/EGM/'
    scenario_list = pd.read_csv(scenario_dirname + 'ScenarioList.csv')
    
    # Get parameters related to scenario
    scenario = scenario_list[scenario_list.name == scenario_name]

    # Catch if name not found
    if scenario.shape[0] == 0:
        print('No scenario with name ' + scenario_name)
        return
    # Create save data folder if does not exist
    if not os.path.exists(scenario.save_data_location.values[0]):
        os.mkdir(scenario.save_data_location.values[0])
    # Load path definition in matlab
    # TODO: This file need to be generated or should exist
    eng.run(top_dirname + 'matlab_pathdef',nargout=0)
    eng.addpath(scenario.folder_location.values[0])
    eng.addpath(scenario.data_location.values[0])
    eng.workspace['save_data_location'] = scenario.save_data_location.values[0]
    eng.workspace['start_index'] = int(scenario.start_index.values[0])
    eng.workspace['end_index'] = int(scenario.end_index.values[0])
    # Run scenario
    eng.run(scenario_name,nargout=0)

    eng.rmpath(scenario.data_location.values[0])
    eng.rmpath(scenario.folder_location.values[0])
    eng.quit()

if __name__ == "__main__":
    import sys
    launch_scenario_performance(sys.argv[1])
