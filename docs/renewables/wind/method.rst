From Wind Speed to Power Output
###############################
Once the U and V components of the wind are converted to a non-directional wind speed
magnitude, this speed is converted to power using wind turbine power curves. Since real
wind farms are not currently mapped to a grid network farms, a capacity-weighted average
wind turbine power curve is created for each state based on the turbine types reported
in `EIA Form 860`_. The wind turbine curve for each real wind farm is looked up from a
database of curves (or the *IEC class 2* power curve provided by NREL in the `WIND
documentation`_ is used for turbines without curves in the database), and scaled from
the real hub heights to 80m hub heights using an alpha of 0.15. These height-scaled,
turbine-specific curves are averaged to obtain a state curve translating wind speed to
normalized power. States without wind farms in `EIA Form 860`_ are represented by the
*IEC class 2* power curve.

Each turbine curve represents the instantaneous power from a single turbine for a given
wind speed. To account for spatio-temporal variations in wind speed (i.e. an hourly
average wind speed that varies through the hour, and a point-specific wind speed that
varies throughout the wind farm), a distribution is used: a normal distribution with
standard deviation of 40% of the average wind speed. This distribution tends to boost
the power produced at lower wind speeds (since the power curve in this region is convex)
and lower the power produced at higher wind speeds (since the power curve in this region
is concave as the turbine tops out, and shuts down at higher wind speeds). This tracks
with the wind-farm level data shown in NREL's validation report.


.. _WIND documentation: https://www.nrel.gov/docs/fy14osti/61714.pdf
.. _EIA form 860: https://www.eia.gov/electricity/data/eia860/
