The National Renewable Energy Laboratory (NREL) has developed the Electrification
Futures Study (EFS) to project and study future sectoral demand changes as a result of
impending widespread electrification. As a part of the EFS, NREL has published multiple
reports (dating back to 2017) that describe their process for projecting demand-side
growth and provide analysis of their preliminary results; all of NREL's published EFS
reports can be found `here
<https://www.nrel.gov/analysis/electrification-futures.html>`_. Accompanying their
reports, NREL has published data sets that include hourly load profiles that were
developed using processes described in the EFS reports. These hourly load profiles
represent state-by-state end-use electricity demand across four sectors
(Transportation, Residential Buildings, Commercial Buildings, and Industry) for three
electrification scenarios (Reference, Medium, and High) and three levels of technology
advancements (Slow, Moderate, and Rapid). Load profiles are provided for six separate
years: 2018, 2020, 2024, 2030, 2040, and 2050. The base demand data sets and further
accompanying information can be found `here <https://data.nrel.gov/submissions/126>`_.
In addition to demand growth projections, NREL has also published data sets that
include hourly profiles for flexible load. These data sets indicate the amount of
demand that is considered to be flexible, as determined through the EFS. The
flexibility demand profiles consider two scenarios of flexibility (Base and Enhanced),
in addition to the classifications for each sector, electrification scenario,
technology advancement, and year. The flexible demand data sets and further
accompanying information can be found `here <https://data.nrel.gov/submissions/127>`_.

Widespread electrification can have a large impact on future power system planning
decisions and operation. While increased electricity demand can have obvious
implications for generation and transmission capacity planning, new electrified demand
(e.g., electric vehicles, air source heat pumps, and heat pump water heaters) offers
large amounts of potential operational flexibility to grid operators. This flexibility
by demand-side resources can result in demand shifting from times of peak demand to
times of peak renewable generation, presenting the opportunity to defer generation and
transmission capacity upgrades. To help electrification impacts be considered properly,
this package has the ability to access NREL's EFS demand data sets. Currently, users can
access the base demand profiles, allowing the impacts of demand growth due to vast
electrification to be explored. Users can also access the EFS flexible demand profiles.

The `NREL EFS demand notebook`_ and `NREL EFS flexibility notebook`_, illustrate the
functionality of the various modules developed for obtaining and cleaning the NREL's
EFS demand data.


.. _NREL EFS demand notebook: https://github.com/Breakthrough-Energy/PreREISE/blob/develop/prereise/gather/demanddata/nrel_efs/demo/efs_demand_reference_slow_2030_demo.ipynb
.. _NREL EFS flexibility notebook: https://github.com/Breakthrough-Energy/PreREISE/blob/develop/prereise/gather/demanddata/nrel_efs/demo/efs_base_flexibility_reference_slow_2030_demo.ipynb
