import numpy as np
import pandas as pd
import time
import os
from multiprocessing import Process

import matlab.engine


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
    if not os.path.exists(scenario.output_data_location.values[0]):
        os.mkdir(scenario.output_data_location.values[0])
    # Load path definition in matlab
    # TODO: This file need to be generated or should exist
    # Start matlab engine
    eng = matlab.engine.start_matlab()
    eng.run(top_dirname + 'add_path',nargout=0)
    eng.addpath(scenario.folder_location.values[0])
    eng.addpath(scenario.input_data_location.values[0])
    eng.workspace['output_data_location'] = scenario.output_data_location.values[0]
    eng.workspace['start_index'] = int(scenario.start_index.values[0])
    eng.workspace['end_index'] = int(scenario.end_index.values[0])
    # Run scenario
    eng.run(scenario_name,nargout=0)

    eng.rmpath(scenario.input_data_location.values[0])
    eng.rmpath(scenario.folder_location.values[0])
    eng.quit()

def launch_scenario_performance_parallel(scenario_name,n_pcalls):
    # Load scenario list

    scenario_dirname = '/home/EGM/'
    scenario_list = pd.read_csv(scenario_dirname + 'ScenarioList.csv')
    
    # Get parameters related to scenario
    scenario = scenario_list[scenario_list.name == scenario_name]

    # Catch if name not found
    if scenario.shape[0] == 0:
        print('No scenario with name ' + scenario_name)
        return
    # Create save data folder if does not exist
    if not os.path.exists(scenario.output_data_location.values[0]):
        os.mkdir(scenario.output_data_location.values[0])
    # Load path definition in matlab
    # TODO: This file need to be generated or should exist
    # Start matlab engine
    # Split the index into n_pcall parts
    pcall_list = np.array_split(range(scenario.start_index.values[0],scenario.end_index.values[0]+1),n_pcalls)
    proc = []
    for i in pcall_list:      
        p = Process(target = matlab_call, args=(scenario, int(i[0]), int(i[-1]),))
        p.start()
        proc.append(p)
    for p in proc:
        p.join()
    
def matlab_call(scenario, i_start, i_end):
    top_dirname = os.path.dirname(__file__)
    top_dirname = os.path.join(top_dirname, '../')
    
    eng = matlab.engine.start_matlab()
    eng.run(top_dirname + 'add_path',nargout=0)
    eng.addpath(scenario.folder_location.values[0])
    eng.addpath(scenario.input_data_location.values[0])
    print('output location')
    print(scenario.output_data_location.values[0])
    eng.workspace['output_data_location'] = scenario.output_data_location.values[0]
    eng.workspace['start_index'] = i_start
    eng.workspace['end_index'] = i_end
    # Run scenario
    eng.run(scenario.name.values[0],nargout=0)

    eng.rmpath(scenario.input_data_location.values[0])
    eng.rmpath(scenario.folder_location.values[0])
    eng.quit()

if __name__ == "__main__":
    import sys
    launch_scenario_performance(sys.argv[1])
