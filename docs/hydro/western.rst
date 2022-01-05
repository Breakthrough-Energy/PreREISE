Western
+++++++
Unlike Texas, we don't have access to hourly (or sub-hourly) total generation by state
or even for the whole Western Interconnection. We rely on three different methods to
derive the shape of the hydro profile in California, Wyoming and the rest of the Western Interconnection.

+ **California**: we use the net demand profile as a template. This is supported by data
  from California ISO (see `CAISO outlook`_) showing that the hydro generation profile
  closely follows the net demand profile.
+ **Wyoming**: we simply apply a constant shape curve to avoid peak-hour violation of
  maximum capacity since hydro generators have a small name plate capacities.
+ **other region in the Western Interconnection**: we use the aggregated generation of
  the top 20 US Army Corps managed hydro dams in Northwestern US (primarily located in
  the state of Washington) as the shape of the hydro profile since WA has the most hydro
  generation in the Western Interconnection. The data is obtained via the US Army Corps
  of Engineers Northwestern Division DataQuery Tool 2.0 (see `USACE dataquery`_).


The above curves are then normalized such that the monthly sum in each of the above
regions is equal to the total monthly hydro generation divided by the total hydro
capacity available in the grid model for the region. Note that `EIA form 923` provides
the historical monthly total hydro generation by state.

The `western hydro notebook`_ generates the profile.


.. _CAISO outlook: http://www.caiso.com/TodaysOutlook/Pages/default.aspx
.. _USACE dataquery: https://www.nwd-wc.usace.army.mil/dd/common/dataquery/www/
.. _EIA form 923: https://www.eia.gov/electricity/data/eia923/
.. _western hydro notebook: https://github.com/Breakthrough-Energy/PreREISE/blob/develop/prereise/gather/hydrodata/eia/demo/western_hydro_v2_demo.ipynb
