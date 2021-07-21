From Solar Irradiance to Power Output
#####################################
Naive
^^^^^
Power output is estimated using a simple normalization procedure. For each solar plant
location in the grid model the hourly Global Horizontal Irradiance (GHI) is divided by
the maximum GHI over the period considered. This procedure is referred to as naive since
other factors can possibly affect the conversion from solar radiation at ground to power
such as the temperature at the site as well as many system configuration including
tracking technology.


System Adviser Model
^^^^^^^^^^^^^^^^^^^^
The `System Adviser Model <https://sam.nrel.gov/>`_ (SAM) developed by NREL is used to
estimate the power output of a solar plant. Irradiance data along with other
meteorological parameters must first be retrieved from NSRDB for each plant site. This
information is then fed to the SAM Simulation Core (SCC) and the power output is
retrieved. The `PySAM`_ Python package provides a wrapper around the SAM library. The
`PVWatts v7 <https://nrel-pysam.readthedocs.io/en/master/modules/Pvwattsv7.html>`_
model is used for all the solar plants in the grid. The system size (in DC units) and
the array type (fixed open rack, backtracked, 1-axis and 2-axis) is set for each solar
plant whereas a unique value of 1.25 is used for the DC to AC ratio (see `article
<https://www.eia.gov/todayinenergy/detail.php?id=35372>`_ from EIA on inverter loading
ratios). Otherwise, all other input parameters of the PVWatts model are set to their
default values. `EIA form 860`_ reports the array type used by each solar PV plant. For
each solar plant in our network, the array type is a combination of the three
technology and calculated via the capacity weighted average of the array type of all
the plants in the EIA form that are located in the same state. If no solar plants are
reported in the form for a particular state, we then consider plants belonging to the
same interconnect.


.. _PySAM: https://sam.nrel.gov/software-development-kit-sdk/pysam.html
.. _EIA form 860: https://www.eia.gov/electricity/data/eia860/
