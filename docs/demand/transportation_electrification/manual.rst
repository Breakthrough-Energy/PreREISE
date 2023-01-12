User Manual
###########
Pre-processed input data
^^^^^^^^^^^^^^^^^^^^^^^^

The following data is provided for the user or could be overridden via an input from the user with a different preferred data set.

+ Annual projections of vehicle miles traveled (VMT) are calculated in advance and are
  provided for the user for all Urban Areas in the U.S.  Each state also has a VMT
  projection for the Rural Area in that state.  See Section 3.1 below for calculation
  process details using data from NREL’s Electrification Futures Study and the
  Department of Transportation’s Transportation and Health Indicators.
+ Projections of the fuel efficiency of battery electric vehicles are provided from
  NREL’s Electrification Futures Study, with more detail in Section 3.4 below.
+ Each vehicle type (light-duty vehicles (LDV), light-duty trucks (LDT), medium-duty
  vehicles (MDV), and heavy-duty vehicles (HDV)) has a data set with vehicle trip
  patterns that is used by the algorithm to represent a typical day of driving.  See
  Sections 1 and 2 for more details on the input data from the National Household
  Travel Survey (NHTS) and the Texas Commercial Vehicle Survey.
+ Each typical day of driving is scaled by data from EPA’s MOVES that captures the
  variation in typical driving behavior across (i) urban/rural areas, (ii) weekend/
  weekday patterns, and (iii) monthly driving behavior (e.g. more driving in the summer
  than the winter).


Calling the main Transportation Electrification method
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
With the above input data, the main function call for the transportation module is
``generate_BEV_vehicle_profiles`` and is called using a few user-specified inputs:

1. Charging Strategy (e.g. Immediate charging or Smart charging)
2. Vehicle type (LDV, LDT, MDV, HDV)
3. Vehicle range (whether 100, 200, or 300 miles on a single charge)
4. Model Year
5. Urban Area / Rural Area that is being modelled

Depending on the spatial region included in the broader simulation, the user can run a
script across multiple Urban Areas and Rural Areas to calculate the projected
electricity demand from electrified transportation for the full spatial region.  From
there, a spatial translation mechanism (described next) converts this demand to the
accompanying demand nodes in the base simulation grid.


Spatial translation mechanism – between any two different spatial resolutions 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
We have developed a module called :py:mod:`prereise.utility.translate_zones`. It takes in the shape files of the two spatial resolutions that the user would like to transform into one from the other. Then a transformation matrix that gives the fractions of every region in one resolution onto each region in the other resolution will be generated based on the overlay of two shape files. Finally, the user can simply multiply profiles in its original resolution, such as Urban/Rural Areas, by the transformation matrix to obtain profiles in the resultant resolution, such as load zones in the base simulation grid. This allows each module to be built in whatever spatial resolution is best for that module and to then transform each module into a common spatial resolution that is then used by the multi-sector integrated energy systems model.   
