import datetime
import os
from multiprocessing import Process
from timeit import default_timer as timer

import matlab.engine
import numpy as np
import pandas as pd

# global variables
scenario_dirname = '/home/EGM/'
scenario_list = pd.read_csv(scenario_dirname + 'ScenarioList.csv')


def launch_scenario_performance(scenario_name, n_pcalls=1):
    """
    This function launches the scenario.
    The scenario is launched in parallel if n_pcalls > 1.
    The function calls scenario_matlab_call in n_pcalls parallel calls.
    
    :param scenario_name: name of the scenario.
    :param n_pcalls: Number of parallel runs.
    """

    # Get parameters related to scenario
    scenario = scenario_list[scenario_list.name == scenario_name]

    # Catch if name not found
    if scenario.shape[0] == 0:
        print('No scenario with name ' + scenario_name)
        return
    # Create save data folder if does not exist
    if not os.path.exists(scenario.output_data_location.values[0]):
        os.mkdir(scenario.output_data_location.values[0])

    i_start = int(scenario.start_index.values[0])
    i_end = int(scenario.end_index.values[0])

    if i_start < 1:
        os.error('i_start has to be greater than 1')
    if i_start > i_end:
        os.error('i_end larger than i_start')
    if n_pcalls > (i_end-i_start + 1):
        os.error('n_pcalls is larger than the number of intervals')

    # Split the index into n_pcall parts
    pcall_list = np.array_split(range(i_start, i_end+1), n_pcalls)
    proc = []
    start = timer()
    for i in pcall_list:
        p = Process(target=scenario_matlab_call, args=(
            scenario, int(i[0]), int(i[-1]),))
        p.start()
        proc.append(p)
    for p in proc:
        p.join()
    end = timer()
    print('Run time: ' + str(datetime.timedelta(seconds=(end-start))))


def scenario_matlab_call(scenario, i_start, i_end):
    """
    It reads the scenario list file that contains all the information
    related to the scenario. The function starts a MATLAB engine,
    runs the add_path file to load MATPOWER and GUROBI.
    It loads the data path and runs the scenario.
    
    :param scenario: The scenario pandas data frame to be launched.
    :param i_start: Start index.
    :param i_end: End index.
    """
    # Location of add_path file
    top_dirname = os.path.dirname(__file__)

    eng = matlab.engine.start_matlab()
    # Load path definition in MATLAB (MATPOWER and GUROBI)
    eng.run(top_dirname + '/add_path', nargout=0)
    eng.addpath(scenario.folder_location.values[0])
    eng.addpath(scenario.input_data_location.values[0])
    eng.workspace['output_data_location'] = \
        scenario.output_data_location.values[0]
    eng.workspace['start_index'] = i_start
    eng.workspace['end_index'] = i_end
    # Run scenario
    eng.run(scenario.name.values[0], nargout=0)

    eng.rmpath(scenario.input_data_location.values[0])
    eng.rmpath(scenario.folder_location.values[0])
    eng.quit()


if __name__ == "__main__":
    import sys
    launch_scenario_performance(sys.argv[1])
