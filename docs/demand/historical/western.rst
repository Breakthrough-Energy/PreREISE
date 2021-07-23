Western
#######
Balancing authorities (BAs) submit their demand data to EIA and can be downloaded
using an `API <https://www.eia.gov/opendata/>`_. The list of BAs in the Western
Interconnection can be found on the website of the Western Electricity Coordinating
Council (WECC) along with the area they approximately cover (see `map`_).

Some data processing/cleaning is then carried out to derive the profile for the Western
Interconnection:

+ adjacent data are used to fill out missing values
+ BAs are aggregated into the load zones of the grid model
+ outliers are detected and fixed.

These steps are illustrated in the `western demand notebook`_.


.. _map: https://www.wecc.org/Administrative/Balancing_Authorities_JAN17.pdf
.. _western demand notebook: https://github.com/Breakthrough-Energy/PreREISE/blob/develop/prereise/gather/demanddata/eia/demo/western_demand_v4_demo/western_demand_v4_demo.ipynb
