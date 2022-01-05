Eastern
+++++++
Profile generation for the Eastern Interconnection is slightly more complex than for
the Western Interconnection. First, we handle pumped storage hydro (HPS) and
conventional hydro (HYC) separately. Then, in addition to using the net demand profile
to derive the profile of conventional hydro plants in some state as we did for
California, we also use historical hourly total hydro generation time series in some
regions.


+ **Pumped Storage Hydro**: We identified hydro plants in our grid model that
  are closely located to known HPS site in the Eastern Interconnection and created a
  template to describe the hourly energy generation. The plant level profile is
  generated considering the local time and daylight-saving schedule of the
  corresponding bus location.
+ **Conventional hydro**: profiles provided by `ISONE`_, `NYISO`_, `PJM`_ and `SPP`_
  are used for plants located within the area they cover. For states that are not at
  all covered or partially covered by the 4 ISOs the net demand demand is used as a
  template to derive the hydro profile using the same method that has been developed
  for California, i.e., the monthly net demand is normalized such that its
  sum is equal to the historical monthly total hydro generation (reported in `EIA form
  923`_) divided by the available total hydro capacity in the grid model. Note that for
  partially covered states, the historical monthly total hydro generation in the state
  is split proportionally to the available total hydro capacity in the grid model for
  the state and only the portion outside the ISOs is used during the normalization.


The `eastern hydro notebook`_ generates the profile.


.. _ISONE: https://www.iso-ne.com/isoexpress/
.. _NYISO: http://mis.nyiso.com/public/P-63list.htm
.. _PJM: http://dataminer2.pjm.com/feed/gen_by_fuel
.. _SPP: https://marketplace.spp.org/pages/generation-mix-historical
.. _eastern hydro notebook: https://github.com/Breakthrough-Energy/PreREISE/blob/develop/prereise/gather/hydrodata/eia/demo/eastern_hydro_v3_demo/eastern_hydro_v3_demo.ipynb
