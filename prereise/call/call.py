
from prereise.call import const

import datetime
import matlab.engine
import numpy as np
import os
import pandas as pd

from collections import OrderedDict
from multiprocessing import Process
from timeit import default_timer as timer


def get_scenario(scenario_id):
    """Returns scenario information.

    :param int scenario_id: scenario index.
    :return: (*dict*) -- scenario information.
    """
    scenario_list = pd.read_csv(const.SCENARIO_LIST)
    scenario_list.fillna('', inplace=True)
    scenario_list.astype(str)
    scenario = scenario_list[scenario_list.id == scenario_id]

    return scenario.to_dict('records', into=OrderedDict)[0]


def launch_scenario_performance(scenario_id, n_pcalls=1):
    """Launches the scenario.

    :param int scenario_id: scenario index.
    :param int n_pcalls: number of parallel runs. The scenario is launched \
        in parallel if n_pcalls > 1. This function calls \
        :func:scenario_matlab_call.
    """

    scenario = get_scenario(scenario_id)

    start_index = int(scenario_info['start_index']) + 1
    end_index = int(scenario_info['end_index']) + 1
    if start_index < 1:
        os.error('start_index < 1')
    if start_index > end_index:
        os.error('end_index > first_index')
    if n_pcalls > (end_index - start_index + 1):
        os.error('n_pcalls is larger than the number of intervals')

    # Create save data folder if does not exist
    output_dir = os.path.join(const.EXECUTE_DIR,
                              'scenario_%s/output' % scenario['id'])
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    # Split the index into n_pcall parts
    pcall_list = np.array_split(range(start_index, end_index + 1), n_pcalls)
    proc = []
    start = timer()
    for i in pcall_list:
        p = Process(target=scenario_matlab_call,
                    args=(scenario, int(i[0]), int(i[-1]),))
        p.start()
        proc.append(p)
    for p in proc:
        p.join()
    end = timer()

    runtime = str(datetime.timedelta(seconds=(end - start)))
    print('Run time: %s' % runtime)


def scenario_matlab_call(scenario, start_index, end_index):
    """Reads the scenario list, starts a MATLAB engine, runs the add_path \
        file to load MATPOWER and GUROBI. Then, loads the data path and \
        runs the scenario.

    :param dict scenario: scenario information.
    :param int start_index: start index.
    :param int end_index: end index.
    """
    # Location of add_path file
    top_dirname = os.path.dirname(__file__)
    eng = matlab.engine.start_matlab()

    # Load path definition in MATLAB (MATPOWER and GUROBI)
    eng.run(top_dirname + '/add_path', nargout=0)
    input_dir = os.path.join(const.EXECUTE_DIR,
                             'scenario_%s' % scenario['id'])
    output_dir = os.path.join(const.EXECUTE_DIR,
                              'scenario_%s/output' % scenario['id'])

    eng.addpath(input_dir)

    eng.workspace['output_data_location'] = output_dir
    eng.workspace['start_index'] = start_index
    eng.workspace['end_index'] = end_index

    # Run scenario
    eng.addpath(const.SCENARIO_MATLAB)
    eng.run('scenario_matlab_script', nargout=0)

    eng.rmpath(input_dir)
    eng.quit()


if __name__ == "__main__":
    import sys

    launch_scenario_performance(sys.argv[1])
