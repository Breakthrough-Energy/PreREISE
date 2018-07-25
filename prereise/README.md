# PreREISE
This package defines the scenario and calls the matlab simulation engine.
## Creation of a scenario
A scenario can be defined by adding an entry to the scenario list table. 
This is currently ScenarioList.csv.
Make sure you choose an unique name. Since this list is temporary an will be replaced by a database there is no check of uniqueness.
Make sure you have stored the scenario_name.m file and the related simulation and data files in the defined folder locations.
## Call the simulation engine.
After setting up the scenario, the simulation engine can be called.
## Setup
This package requires matlab and matpower. 
### For matlab the following setup is required:
On Windows systems —
cd "matlabroot\extern\engines\python"
python setup.py install
On Mac or Linux systems —
cd "matlabroot/extern/engines/python"
python setup.py install
### For matpower the following setup is required:
Add the following directories to your MATLAB path:
<MATPOWER>        — core MATPOWER functions
<MATPOWER>/most   — core MOST functions

or run install_matpower.m in matlab

Save your matlab path to a file with the name matlab_pathdef.m and place it in the top directory.

