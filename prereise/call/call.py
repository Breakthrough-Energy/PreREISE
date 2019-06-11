from prereise.call import const

import datetime
import math
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
    scenario_list = pd.read_csv(const.SCENARIO_LIST, dtype=str)
    scenario_list.fillna('', inplace=True)
    scenario = scenario_list[scenario_list.id == scenario_id]

    return scenario.to_dict('records', into=OrderedDict)[0]

def insert_in_file(filename, scenario_id, column_number, column_value):
    """Updates status in execute list on server.

    :param str filename: path to execute or scenario list.
    :param str scenario_id: scenario index.
    :param str column_number: id of column (indexing starts at 1).
    :param str column_value: value to insert.
    """
    options = "-F, -v OFS=',' -v INPLACE_SUFFIX=.bak -i inplace"
    program = ("'{for(i=1; i<=NF; i++){if($1==%s) $%s=\"%s\"}};1'" %
               (scenario_id, column_number, column_value))
    command = "awk %s %s %s" % (options, program, filename)
    os.system(command)

def launch_scenario_performance(scenario_id, n_pcalls=1):
    """Launches the scenario.

    :param int scenario_id: scenario index.
    :param int n_pcalls: number of parallel runs. The scenario is launched \
        in parallel if n_pcalls > 1. This function calls \
        :func:scenario_matlab_call.
    :raises Exception: if indices are improperly set.
    """

    scenario_info = get_scenario(scenario_id)

    min_ts = pd.Timestamp('2016-01-01 00:00:00')
    max_ts = pd.Timestamp('2016-12-31 23:00:00')
    dates = pd.date_range(start=min_ts, end=max_ts, freq='1H')

    start_ts = pd.Timestamp(scenario_info['start_date'])
    end_ts = pd.Timestamp(scenario_info['end_date'])

    # MATLAB starts at 1
    start_index = dates.get_loc(start_ts) + 1
    end_index = dates.get_loc(end_ts) + 1

    # Create save data folder if does not exist
    output_dir = os.path.join(const.EXECUTE_DIR,
                              'scenario_%s/output' % scenario_info['id'])
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    # Update status in ExecuteList.csv
    insert_in_file(const.EXECUTE_LIST, scenario_info['id'], '2', 'running')

    # Split the index into n_pcall parts
    pcall_list = np.array_split(range(start_index, end_index + 1), n_pcalls)
    proc = []
    start = timer()
    for i in pcall_list:
        p = Process(target=scenario_matlab_call,
                    args=(scenario_info, int(i[0]), int(i[-1]),))
        p.start()
        proc.append(p)
    for p in proc:
        p.join()
    end = timer()

    # Update status in ExecuteList.csv
    insert_in_file(const.EXECUTE_LIST, scenario_info['id'], '2', 'finished')

    runtime = datetime.timedelta(seconds=(end - start))
    print('Run time: %s' % str(runtime))
    insert_in_file(const.SCENARIO_LIST, scenario_info['id'], '14',
                "%s:%s" % (runtime.seconds//3600, (runtime.seconds//60)%60))


def scenario_matlab_call(scenario_info, start_index, end_index):
    """Reads the scenario list, starts a MATLAB engine, runs the add_path \
        file to load MATPOWER and GUROBI. Then, loads the data path and \
        runs the scenario.

    :param dict scenario_info: scenario information.
    :param int start_index: start index.
    :param int end_index: end index.
    """

    # Location of add_path file
    top_dirname = os.path.dirname(os.path.abspath(__file__))
    eng = matlab.engine.start_matlab()

    # Load path definition in MATLAB (MATPOWER and GUROBI)
    eng.run(top_dirname + '/add_path', nargout=0)
    input_dir = os.path.join(const.EXECUTE_DIR,
                             'scenario_%s' % scenario_info['id'])
    output_dir = os.path.join(const.EXECUTE_DIR,
                              'scenario_%s/output/' % scenario_info['id'])

    eng.addpath(input_dir)

    eng.workspace['output_data_location'] = output_dir
    eng.workspace['start_index'] = start_index
    eng.workspace['end_index'] = end_index
    eng.workspace['interval'] = int(scenario_info['interval'].split('H', 1)[0])
    # Run scenario

    eng.addpath(const.SCENARIO_MATLAB)
    eng.run('scenario_matlab_script', nargout=0)

    eng.rmpath(input_dir)
    eng.quit()


if __name__ == "__main__":
    import sys

    launch_scenario_performance(sys.argv[1])
