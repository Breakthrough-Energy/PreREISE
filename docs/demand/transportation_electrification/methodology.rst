Methodology 
###########

.. _ev_charging_model:

EV Charging Model Process and Flowchart 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
This EV charging model simulates the charging behavior of the following on-road vehicle
categories: LDV, LDT, MDV, and HDV. The default LDV and LDT trip data come from the 2017
NHTS, with an example of the data included in :numref:`example_daily_trips`.

.. _example_daily_trips:

.. figure:: demand/transportation_electrification/img/methodology/daily_trips.png
   :align: center

   Example daily trips of vehicle data from NHTS

These are also divided into Census Divisions, which are then mapped to the corresponding
regions within the grid model. The MDV and HDV trip data are anonymized from the Texas
Commercial Vehicle Survey and calibrated to align with medium- and heavy-duty vehicle
trip statistics. More details about each data set are included in
:numref:`vehicle_travel_patterns` and can be updated to reflect different vehicle
scenarios or incorporate more recent data. In all cases, an average weekday and average
weekend daily pattern of vehicle trips is calculated from the vehicle trip data. Then,
these trips are filtered by vehicle type (e.g. LDV, LDT, MDV, and HDV) and by range for
LDVs and LDTs (e.g. less than 100 miles, less than 200 miles, less than 300 miles) to
capture what is capable for typical battery capacities.  This creates a weekday and
weekend daily pattern of BEV-capable trips that will be used in the subsequent steps.
The LDV and LDT vehicle miles traveled (VMT) by hour is presented in
:numref:`vmt_by_hour`.

.. _vmt_by_hour:

.. figure:: demand/transportation_electrification/img/methodology/vmt_by_hour.png
   :align: center

   Light-duty vehicle/truck miles traveled by hour of the day for weekends and weekdays 

Similarly, Figure :numref:`dwelling_over_24h` illustrates the percentage of vehicles
parked and able to charge at each hour over a 24-hour period. 

.. _dwelling_over_24h:

.. figure:: demand/transportation_electrification/img/methodology/dwelling_over_24h.png
   :align: center

   Status of dwelling vehicles over 24-hour period

The flowchart in :numref:`trip_patterns_flowchart` illustrates the entire procedure.

.. _trip_patterns_flowchart:

.. mermaid::
   :caption: Workflow from input trip data to weekday and weekend trip patterns 

   flowchart TD
      subgraph main[ ]
        subgraph input[ ]
          A(Input: NHTS trip data for LDV/LDT)
          B(Input: Anonymized trip data for MDV/HDV)
        end
        A==>C(Divide into census region)
        C==>D(Create weekday and weekend pattern of typical vehicle trips)
        B==>D
        D==>E("Filter trips by range [0,100, 0,200, 0,300] miles")
        E==>F(Create weekday and weekend pattern of BEV-capable trips)
      end

      class input white_no_border
      class main,A,B,C,D,E,F white
      classDef white fill:#ffffff,stroke:#333,stroke-width:3px
      classDef white_no_border fill:#ffffff,stroke:#333,stroke-width:0px

These daily BEV-capable trip patterns are then further distributed temporally and
spatially, as discussed in more detail in :numref:`annual_vehicle_miles_traveled`.
State-level and UA VMT per capita were taken from the Department of Transportation’s
transportation health tool and create the distribution across rural and urban areas, as
defined by the U.S. Census Bureau :cite:p:`DoT_transportation_health_tool`,
:cite:p:`CB_urban_rural_classification`. Weight factors from the U.S. EPA model, MOVES,
create the time-of-year scaling of weekday versus weekend and month of the year
:cite:p:`EPA_moves`.
 
Projections from NREL’s EFS provide the adoption rate scaling of BEV demand to create
the base-year and simulation-year profiles of BEV-capable trip patterns
:cite:p:`NREL_electric_technology_adoption`. Total charging demand by area (urban and
rural) is scaled based on state-level BEV VMT projections from NREL’s EFS.  As more
granular BEV projections become available, scaling projections could be targeted to
specific urban and rural areas given the model’s structure. The procedure is shown in
:numref:`dynamics_flowchart`.

.. _dynamics_flowchart:

.. mermaid::
   :caption: Workflow from weekday and weekend trip patterns to annual VMT pattern

   flowchart LR
      subgraph main[ ]
        direction TB
        subgraph start[ ]
          A(Weekday and weekend pattern <br> of BEV-capable trips)
        end
        subgraph input[ ]
          direction LR
          B(Input: census population data <br> for urban area and states)
          C(Input: DoT Transportation and Health Tool's <br> VMT per capita for urban areas and states)
          B------C
        end
        A====input
        D(Convert state-level VMT per capita into one <br> year's total of urban and rural driving for each state)
        input==>D
        subgraph middle[ ]
          direction LR
          E(Annual amount of VMT is distributed <br> across weeks and months based on <br> driving data from EPA's MOVES)
          F(Input: EPA's MOVES for weekday/weekend <br> and monthly VMT distributions)
          F----E
        end
          D==>middle
        subgraph last[ ]
          direction LR
          G(Create a base-year and simulation-year profile <br> of BEV-capable trips by scaling annual VMT <br> to match NREL's EFS projections)
          H(Input: NREL's EFS projections of <br> future BEV adoption rates)
          H----G
        end
        middle==>last
      end

      class main,A,input,B,C,D,middle,E,F,last,G,H white
      class start white_no_border
      classDef white fill:#ffffff,stroke:#333,stroke-width:3px
      classDef white_no_border fill:#ffffff,stroke:#333,stroke-width:0px

Algorithmically, these projections are modeled by making multiple copies of individual
trips, as illustrated in :numref:`scaling_process_vehicle_trip`, which are used in the
smart charging algorithm. 

.. _scaling_process_vehicle_trip:

.. figure:: demand/transportation_electrification/img/methodology/scaling_process_vehicle_trip.png
   :align: center

   Scaling process of vehicle trip

With the projected BEV vehicle trips in place, NREL’s EFS is again used to set the fuel
efficiency for the simulated year to determine the amount of electricity needed to
charge after each BEV trip.  Then, the charging model uses one of two charging algorithm
strategies: immediate (uncoordinated) charging and smart (optimal) charging, with
example illustrations shown in :numref:`immediate_charging_result` and
:numref:`smart_charging_result`. Both algorithms are deterministic and directly utilize
the input vehicle trip data to calculate the charging demand based on vehicle travel
distances, dwell locations, and user defined infrastructure parameters. The Smart
Charging algorithm currently uses an optimization function to minimize wholesale prices
via flattening the net load curve. Incorporating additional optimization goals that will
change the cost function, such as minimizing individual vehicle costs in response to
time-varying utility rate structures, could be explored in future work. For the Smart
Charging algorithm, each representative vehicle sequentially sets its charging pattern
in response to the optimization function as well as an aggregate load profile. That
vehicle’s additional charging load is then added to the aggregate load profile, which is
then sent to the next vehicle as an input to its smart charging decision. The aggregate
profile of electricity demand from all smart-charging BEVs is then simply the sum across
all vehicles (see :numref:`demand_calculation_flowchart`). 

.. _demand_calculation_flowchart:

.. mermaid::
   :caption: Workflow from the annual VMT pattern to the additional electricity demand from the BEV charging profiles 

   flowchart TB
      subgraph main[ ]
        direction TB
        subgraph input[ ]
          direction RL
          A(Base-year and simulation-year <br> profile of BEV trips)
          B(Input: NREL's EFS for fuel efficiency <br> projections by vehicle type)
          B---->A
         end
         C(Fuel efficiency projections determine <br> charging needed after each vehicle trip)
        input==>C
        D(Charging algorithm: immediate and smart)
        C==>D
        E(Create a simulation-year profile <br> of electricity demand from <br> transportation electrification)
        D==>E
      end

      class main,input,A,B,C,D,E white
      classDef white fill:#ffffff,stroke:#333,stroke-width:3px
      classDef white_no_border fill:#ffffff,stroke:#333,stroke-width:0px


Immediate and Smart Charging Example Outputs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Immediate Charging refers to full power charging at time of plug-in until full capacity
reached or car unplugged, whichever comes first.

.. _immediate_charging_result:

.. figure:: demand/transportation_electrification/img/methodology/immediate_charging_result.png
   :align: center

   Notional results for immediate charging algorithm, with charging hours within the
   bracket

Smart charging refers to coordinated charging, where drivers provide information on
their travel schedule and charging demand to the electric grid operator.

.. _smart_charging_result:

.. figure:: demand/transportation_electrification/img/methodology/smart_charging_result.png
   :align: center

   Notional results for smart charging algorithm, with charging hours within the
   bracket 


**Example Output -- Immediate Charging**. Immediate Charging refers to full power
charging at time of plug-in until the battery is full or until the vehicle departs on
the next driving trip. :numref:`ldv_immediate_charging_output` presents a normalized,
unscaled LDV charging demand alongside a normalization of the underlying
non-transportation base demand (note: the normalization of the charging profile uses the
sum of a full year of charging from the sample vehicles as the denominator).  Notice how
the uncoordinated charging pattern aligns with the underlying non-transportation base
demand.

From there, this normalized profile is then scaled based on the parameters for the
desired simulation year, with an example output shown in
:numref:`example_ldv_immediate_load`. These parameters include the projected VMT for the
simulated year, the fuel efficiency projection (e.g. number of kWh consumed per mile
traveled), and the efficiency of the charging process. Notice that the peak demand
increases due to the uncoordinated charging pattern. 

.. _ldv_immediate_charging_output:

.. figure:: demand/transportation_electrification/img/methodology/ldv_immediate_charging_output.png
   :align: center

   Normalized LDV Immediate Charging output for 1 example week


**Example Output -- Smart Charging**. Smart charging refers to coordinated charging,
where drivers provide information on their travel schedule and charging demand to the
electric grid operator. Vehicle charging is optimized based on cost (e.g., time-of-use
rates), grid support needs, travel considerations, and vehicle constraints.
:numref:`ldv_smart_charging_output` presents a normalized, unscaled LDV smart charging
demand alongside a normalization of the underlying non-transportation base demand.
Notice how in this case the smart charging pattern no longer aligns with the underlying
non-transportation base demand. :numref:`example_ldv_smart_load` shows an example of the
results from LDV smart charging at scale that was optimized for grid support needs by
flattening net demand (e.g. “filling in the valleys”). 

.. _ldv_smart_charging_output:

.. figure:: demand/transportation_electrification/img/methodology/ldv_smart_charging_output.png
   :align: center

   Normalized LDV Smart Charging output for 1 example week


.. _vehicle_travel_patterns:

Vehicle Travel Patterns
^^^^^^^^^^^^^^^^^^^^^^^
Light-duty Travel patterns
~~~~~~~~~~~~~~~~~~~~~~~~~~
The 2017 National Household Travel Survey (NHTS) documents the light-duty vehicle and
light-duty truck travel patterns (https://nhts.ornl.gov/). Data from the NHTS 2017
``trippub.csv`` dataset were filtered to identify all vehicle trips. Relevant data were
then divided into nine datasets, one for each Census Division, as defined within the
dataset, see :numref:`census_divisions_table`.

.. _census_divisions_table:

.. table:: Census divisions

    +----------------+--------------------+--------------------------------------+
    | Division Number| Name               | States Included                      |
    +================+====================+======================================+
    | 01             | New England        | CT, MA, ME, NH, RI, VT               |
    +----------------+--------------------+--------------------------------------+
    | 02             | Middle Atlantic    | PA, NJ, NY                           |
    +----------------+--------------------+--------------------------------------+
    | 03             | East North Central | IL, IN, MI, OH, WI                   |
    +----------------+--------------------+--------------------------------------+
    | 04             | West North Central | IA, KS, MN, MO, ND, NE, SD           |
    +----------------+--------------------+--------------------------------------+
    | 05             | South Atlantic     | DE, FL, GA, MD, NC, SC, VA, WV, (DC) |
    +----------------+--------------------+--------------------------------------+
    | 06             | East South Central | AL, KY, MS, TN                       |
    +----------------+--------------------+--------------------------------------+
    | 07             | West South Central | AR, LA, OK, TX                       |
    +----------------+--------------------+--------------------------------------+
    | 08             | Mountain           | AZ, CO, ID, MT, NM, NV, UT, WY       |
    +----------------+--------------------+--------------------------------------+
    | 09             | Pacific            | AK, CA, HI, OR, WA                   |
    +----------------+--------------------+--------------------------------------+

The definition for each column in the final datasets is in
:numref:`nhts_trip_dataset_table`. Columns 1-20 are taken directly from the NHTS
dataset, and columns 21-28 are calculated values based on the preceding columns. 

.. _nhts_trip_dataset_table:

.. table:: Columns in modified NHTS trip Dataset

    +--------+--------------------------------+
    | Column | Variable                       |
    +========+================================+
    | 1      | Household                      |
    +--------+--------------------------------+
    | 2      | Vehicle ID                     |
    +--------+--------------------------------+
    | 3      | Person ID                      |
    +--------+--------------------------------+
    | 4      | Scaling Factor Applied         |
    +--------+--------------------------------+
    | 5      | Trip Number                    |
    +--------+--------------------------------+
    | 6      | Date (YYYYMM)                  |
    +--------+--------------------------------+
    | 7      | Day of Week (1 - 7)            |
    +--------+--------------------------------+
    | 8      | If Weekend                     |
    +--------+--------------------------------+
    | 9      | Trip Start Time (HHMM)         |
    +--------+--------------------------------+
    | 10     | Trip End Time (HHMM)           |
    +--------+--------------------------------+
    | 11     | Travel Minutes                 |
    +--------+--------------------------------+
    | 12     | Dwell Time                     |
    +--------+--------------------------------+
    | 13     | Miles Traveled                 |
    +--------+--------------------------------+
    | 14     | Vehicle Miles Traveled         |
    +--------+--------------------------------+
    | 15     | Why From                       |
    +--------+--------------------------------+
    | 16     | Why To                         |
    +--------+--------------------------------+
    | 17     | Vehicle Type (1-4 LDV, 5+ LDT) |
    +--------+--------------------------------+
    | 18     | Household Vehicle Count        |
    +--------+--------------------------------+
    | 19     | Household Size                 |
    +--------+--------------------------------+
    | 20     | Trip Type                      |
    +--------+--------------------------------+
    | 21     | Start Time (hour decimal)      |
    +--------+--------------------------------+
    | 22     | End Time (hour decimal)        |
    +--------+--------------------------------+
    | 23     | Dwell Time (hour decimal)      |
    +--------+--------------------------------+
    | 24     | Travel Time (hour decimal)     |
    +--------+--------------------------------+
    | 25     | Vehicle Speed (mi/hour)        |
    +--------+--------------------------------+
    | 26     | Sample Vehicle Number          |
    +--------+--------------------------------+
    | 27     | Total Vehicle Trips            |
    +--------+--------------------------------+
    | 28     | Total Vehicle Miles Traveled   |
    +--------+--------------------------------+

Total vehicle trips variable refers to the total number of trips a single vehicle takes
in the sample window (24 hours). Trips are divided into weekday and weekend trips. The
resulting charging profile for each day type is replicated across the year, i.e., each
weekday and each weekend are the same set of trips across the year.
:numref:`trip_count_table` presents the total number of trips in the trip datasets for
each vehicle category. The weekday and weekend trips are weighted based on the MOVES
weight factors. The charging demand is scaled up and down further based on the MOVES
monthly weight factors depending on the month of the year.

.. _trip_count_table:

.. table:: Trip count by vehicle category, census division, and day of week

    +------------------+-----------------+-------------------+
    | Vehicle Category | Census Division | Trip Count        |
    +                  +                 +---------+---------+
    |                  |                 | Weekday | Weekend |
    +==================+=================+=========+=========+
    | LDV              | 01              | 3979    | 1235    |
    +                  +-----------------+---------+---------+
    |                  | 02              | 32831   | 10664   |
    +                  +-----------------+---------+---------+
    |                  | 03              | 30815   | 5116    |
    +                  +-----------------+---------+---------+
    |                  | 04              | 8962    | 2885    |
    +                  +-----------------+---------+---------+
    |                  | 05              | 58173   | 9620    |
    +                  +-----------------+---------+---------+
    |                  | 06              | 2294    | 611     |
    +                  +-----------------+---------+---------+
    |                  | 07              | 52982   | 7818    |
    +                  +-----------------+---------+---------+
    |                  | 08              | 9127    | 2033    |
    +                  +-----------------+---------+---------+
    |                  | 09              | 53554   | 16386   |
    +------------------+-----------------+---------+---------+
    +------------------+-----------------+---------+---------+
    | LDT              | 01              | 2881    | 935     |
    +                  +-----------------+---------+---------+
    |                  | 02              | 29513   | 9347    |
    +                  +-----------------+---------+---------+
    |                  | 03              | 31788   | 5478    |
    +                  +-----------------+---------+---------+
    |                  | 04              | 10157   | 2960    |
    +                  +-----------------+---------+---------+
    |                  | 05              | 58900   | 9465    |
    +                  +-----------------+---------+---------+
    |                  | 06              | 2416    | 678     |
    +                  +-----------------+---------+---------+
    |                  | 07              | 60929   | 8530    |
    +                  +-----------------+---------+---------+
    |                  | 08              | 10006   | 2084    |
    +                  +-----------------+---------+---------+
    |                  | 09              | 40161   | 12116   |
    +------------------+-----------------+---------+---------+
    +------------------+-----------------+---------+---------+
    | MDV              | All             | 8302    | same    |
    +------------------+-----------------+---------+---------+
    +------------------+-----------------+---------+---------+
    | HDV              | All             | 8407    | same    |
    +------------------+-----------------+---------+---------+

Medium- and Heavy-duty Vehicles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The construction of the original representative datasets is described in
:cite:p:`2020:forest`.  

The following is a description of the data that are rendered from the initial,
representative HDV dataset.  

1.  Trip times, trip count, and miles traveled – data on trips was taken from the
    original trip datasets and scaled to align with known statistics for the target
    region.  Only trip count, times, and miles traveled were included. Information on
    locations, vehicle identity, vehicle class, and vocation are excluded. 
2.  Dwell location – dwell locations are simplified to being either a “home base
    location” or not. Home base locations are defined as depots that are owned, managed,
    and/or under contract with the same entity as the fleet vehicle.  
3. Trip start and stop times – travel and dwell times by time of day. 

The final data table structure is presented in :numref:`mdv_and_hdv_trip_dataset`. Each
row of the data table is a unique trip taken by the specified vehicle. 

.. _mdv_and_hdv_trip_dataset:

.. table:: Columns in modified MDV and HDV trip datasets 

    +--------+--------------------------------+---------------------------------------+
    | Column | Variable                       | Description                           |
    +========+================================+=======================================+
    | 1      | Vehicle Number                 | Unique vehicle number                 |
    +--------+--------------------------------+---------------------------------------+
    | 2      | Trip Number                    | Current trip number of vehicle        |
    +--------+--------------------------------+---------------------------------------+
    | 3      | Destination (home base or not) | Where the trip ends, 1 = home base,   |
    |        |                                | 2 = not home base                     |
    +--------+--------------------------------+---------------------------------------+
    | 4      | Trip Distance                  | Miles traveled in the trip            |
    +--------+--------------------------------+---------------------------------------+
    | 5      | Trip Start                     | Time of trip start                    |
    +--------+--------------------------------+---------------------------------------+
    | 6      | Trip End                       | Time of trip end                      |
    +--------+--------------------------------+---------------------------------------+
    | 7      | Dwell Time                     | Length of time vehicle parked between |
    |        |                                | trips                                 |
    +--------+--------------------------------+---------------------------------------+
    | 8      | Trip Time                      | Length of travel time                 |
    +--------+--------------------------------+---------------------------------------+
    | 9      | Total Vehicle Trips            | Total count of trips taken by the     |
    |        |                                | identified vehicle in the time window |
    +--------+--------------------------------+---------------------------------------+
    | 10     | Total Vehicle Miles            | Total vehicle miles traveled by       |
    |        |                                | vehicle in time window                |
    +--------+--------------------------------+---------------------------------------+



.. _annual_vehicle_miles_traveled:

Annual Vehicle Miles Traveled
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The model is structured for a single base year (2017) and 33 future years (2018-2050).
Each year is unique based on vehicle miles traveled (VMT) and fuel economy (miles per
gallon of gasoline equivalent, mi/GGE), which together determine annual vehicle
electricity demand. The base year and future projections of battery electric vehicle
miles traveled are taken from NREL’s EFS :cite:p:`NREL_electric_technology_adoption`. BEV
VMT is divided into VMT occurring in UAs and RAs. UA is a term assigned by the U.S.
Census Bureau and is described as areas with a population of 50,000 people or more
:cite:p:`CB_urban_rural_classification`. Other years are available from NREL, if
desired.

.. _electric_vehicle_miles_traveled_projections:

Electric Vehicle Miles Traveled Projections by Urban and Rural Area 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
VMT per capita for each state and UA was taken from the Department of Transportation’s 
transportation health tool :cite:p:`DoT_transportation_health_tool`. To determine total 
state VMT, state population was taken from Census data and was multiplied by the above 
state VMT per capita data :cite:p:`DoT_transportation_health_tool` 
:cite:p:`CB_urban_rural_classification`. Then, to calculate the fraction of total state 
VMT that is allocated to each UA and RA, the UA population was also pulled from Census 
data :cite:p:`CB_urban_rural_classification`. From there, the UA population was 
multiplied by UA VMT per capita to get total UA VMT. Lastly, UA VMT is subtracted from 
state VMT to determine the RA VMT for the state. These calculations are summarized 
below: 

.. math::

    V_{\rm state} = A_{\rm state} \times P_{\rm state}

| where:
| :math:`V_{\rm state}` is the state VMT,
| :math:`A_{\rm state}` is the VMT per capita,
| :math:`P_{\rm state}` is the state population.

.. math::

    V_{\rm UA} = A_{\rm UA} \times P_{\rm UA}

| where:
| :math:`V_{\rm UA}` is the urban area VMT,
| :math:`A_{\rm UA}` is the VMT per capita,
| :math:`P_{\rm UA}` is the urban area population.

.. math::

    V_{\rm RA} = A_{\rm state} - \sum V_{\rm UA}

| where:
| :math:`V_{\rm RA}` is the rural area VMT.


Monthly and Daily Weight Factors 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Along with the rural/urban distribution, the default scenarios also use weekday/weekend
and monthly weight factors to distribute annual VMT. These weight factors come directly
from the U.S. EPA’s MOVES model :cite:p:`EPA_moves`. The weight factor values are listed 
in :numref:`weekday_vs_weekend_weight_table` and :numref:`month_weight_table`. 

.. _weekday_vs_weekend_weight_table:

.. table:: Weekday versus weekend weight factors

    +-------------------------------+---------+----------+
    | Day Type                      | Rural   | Urban    |
    +===============================+=========+==========+
    | Weekday (divided over 5 days) | 0.72118 | 0.762365 |
    +-------------------------------+---------+----------+
    | Weekend (divided over 2 days) | 0.27882 | 0.237635 |
    +-------------------------------+---------+----------+

.. _month_weight_table:

.. table:: Month weight factors

    +-----------+---------------+
    | Month     | Weight Factor |
    +===========+===============+
    | January   | 0.0731        |
    +-----------+---------------+
    | February  | 0.0697        |
    +-----------+---------------+
    | March     | 0.0817        |
    +-----------+---------------+
    | April     | 0.0823        |
    +-----------+---------------+
    | May       | 0.0875        |
    +-----------+---------------+
    | June      | 0.0883        |
    +-----------+---------------+
    | July      | 0.0923        |
    +-----------+---------------+
    | August    | 0.0934        |
    +-----------+---------------+
    | September | 0.0847        |
    +-----------+---------------+
    | October   | 0.0865        |
    +-----------+---------------+
    | November  | 0.0802        |
    +-----------+---------------+
    | December  | 0.0802        |
    +-----------+---------------+


.. _bev_vmt_projections:

BEV VMT Projections 
~~~~~~~~~~~~~~~~~~~
To calculate the BEV VMT by vehicle class for each UA, state-level BEV VMT projections
were based on NREL's EFS for 8 vehicle types 
:cite:p:`NREL_electric_technology_adoption`: 

1. LDV BEV Cars: 100 mi, 200 mi, 300 mi 
2. LDV BEV Trucks: 100 mi, 200 mi, 300 mi 
3. MDV Trucks 
4. HDV Trucks 

Projections were used for 2018-2050. The 2017 base year assumptions were calibrated
based on historical data. For all years, BEV VMT at the state level was translated to
BEV VMT at the UA level by multiplying the state-level projections by the fraction of
state VMT allocated to each UA. It is assumed that the proportion of VMT occurring in
urban areas relative to total state VMT will be constant moving into the future. There
are some UAs that did not have VMT data. Out of 481 UAs, 56 did not have VMT per capita
data from the DOT, so those entries will use their respective state’s VMT per capita.

Once each UA and the state’s RA have their projected annual VMT for a simulation year,
the annual VMT is distributed to each day of the year based on weight factors from U.S.
EPA MOVES model, see :numref:`scaling_table`. Each daily weight factor represents the
fraction of annual VMT that is traveled in that specific day. The daily weight factors
vary by month, whether the VMT is in a UA or a RA, and whether the day is a weekday or
a weekend day. For example, within a given urban area all weekdays in January have the
same weight factor and therefore the same allocated VMT.

.. _scaling_table:

.. table:: Urban and rural scaling factors by month and weekday vs weekend

    +-----------+-------------------+-------------------+
    |           | Urban             | Rural             |
    +-----------+---------+---------+---------+---------+
    | Month     | Weekday | Weekend | Weekday | Weekend |
    +===========+=========+=========+=========+=========+
    | January   | 0.00252 | 0.00196 | 0.00238 | 0.00230 |
    +-----------+---------+---------+---------+---------+
    | February  | 0.00266 | 0.00207 | 0.00251 | 0.00243 |
    +-----------+---------+---------+---------+---------+
    | March     | 0.00279 | 0.00218 | 0.00266 | 0.00257 |
    +-----------+---------+---------+---------+---------+
    | April     | 0.00296 | 0.00231 | 0.00268 | 0.00277 |
    +-----------+---------+---------+---------+---------+
    | May       | 0.00299 | 0.00233 | 0.00285 | 0.00275 |
    +-----------+---------+---------+---------+---------+
    | June      | 0.00313 | 0.00244 | 0.00297 | 0.00287 |
    +-----------+---------+---------+---------+---------+
    | July      | 0.00321 | 0.00250 | 0.00301 | 0.00291 |
    +-----------+---------+---------+---------+---------+
    | August    | 0.00319 | 0.00249 | 0.00304 | 0.00294 |
    +-----------+---------+---------+---------+---------+
    | September | 0.00302 | 0.00236 | 0.00285 | 0.00276 |
    +-----------+---------+---------+---------+---------+
    | October   | 0.00298 | 0.00232 | 0.00282 | 0.00272 |
    +-----------+---------+---------+---------+---------+
    | November  | 0.00284 | 0.00221 | 0.00270 | 0.00261 |
    +-----------+---------+---------+---------+---------+
    | December  | 0.00279 | 0.00217 | 0.00262 | 0.00253 |
    +-----------+---------+---------+---------+---------+

The trip data are scaled based on the allocated daily VMT. The daily patterns are
adjusted by scaling the VMT of each trip within the daily patterns so that the total
across the simulation matches the Annual VMT projection for each state. 

.. _fuel_efficiency_projections:

Fuel Efficiency Projections 
~~~~~~~~~~~~~~~~~~~~~~~~~~~
NREL’s Electrification Futures Study also projects average BEV fuel economy over time,
based on assumptions regarding technology improvements and vehicle range
:cite:p:`NREL_efs`. NREL provides a range of possible BEV fuel economies (“Slow
Advancement”, “Moderate Advancement”, and “Rapid Advancement”). The charging model uses
the "Moderate Advancement" values as the default fuel economy for each vehicle category
and year, as shown in :numref:`bev_fuel_economy_table`. 

.. _bev_fuel_economy_table:

.. table:: Default BEV fuel economy by vehicle category and year

    +-------------------------------------+-----------------------------------------------------------+
    |                                     | Fuel Economy (mile/GGE)                                   |
    +                                     +-----------+-----------+-----------+-----------+-----------+
    | Vehicle Type                        | 2017-2019 | 2020-2024 | 2025-2034 | 2035-2044 | 2045-2050 |
    +=====================================+===========+===========+===========+===========+===========+
    | LDV BEV cars, 100 mile range        | 103       | 117       | 137       | 153       | 159       |
    +-------------------------------------+-----------+-----------+-----------+-----------+-----------+
    | LDV BEV cars, 200 mile range        | 97        | 112       | 133       | 149       | 155       |
    +-------------------------------------+-----------+-----------+-----------+-----------+-----------+
    | LDV BEV cars, 300 mile range        | 85        | 102       | 124       | 138       | 144       |
    +-------------------------------------+-----------+-----------+-----------+-----------+-----------+
    | LDT BEV trucks, 100 mile range      | 60        | 69        | 78        | 83        | 85        |
    +-------------------------------------+-----------+-----------+-----------+-----------+-----------+
    | LDT BEV trucks, 200 mile range      | 57        | 66        | 76        | 81        | 83        |
    +-------------------------------------+-----------+-----------+-----------+-----------+-----------+
    | LDT BEV trucks, 300 mile range      | 50        | 60        | 72        | 76        | 79        |
    +-------------------------------------+-----------+-----------+-----------+-----------+-----------+
    | MDV trucks                          | 16        | 17        | 19        | 21        | 22        |
    +-------------------------------------+-----------+-----------+-----------+-----------+-----------+
    | HDV trucks                          | 9         | 10        | 13        | 14        | 15        |
    +-------------------------------------+-----------+-----------+-----------+-----------+-----------+

Smart Charging Optimization Algorithm 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The smart charging algorithm was developed by :cite:p:`2014:zhang`. The algorithm is a
least cost optimization problem, with the cost function as follows:

.. math::

    min \sum_{i=1}^n \sum_{j=1}^{seg(i)} f_{ij} x_{ij}

| where:
| :math:`f` is the cost of electricity in [$/kWh],
| :math:`x` is the increase in vehicle state of charge in [kWh],
| :math:`i` is the dwell period per trip count,
| :math:`seg(i)` is the number of dwell segments for dwell period :math:`i`,
| :math:`j` is the dwell segment in [h],
| :math:`n` is the total number of dwell per trip periods

The total number of dwell segments :math:`seg(i)` will depend on the how long the
vehicle is parked.

**Equality** constraint:

.. math::

    \sum_{i=1}^n \sum_{j=1}^{seg(i)} x_{ij} + \sum_{i=1}^n y_i = 0

| where:
| :math:`y` is the discharged energy from driving

**Inequality** constraints:

.. math::

    y_1 & > -c

    y_1 & + \sum_{j=1}^{seg(1)} x_{1j} + y_2 > -c

    y_1 & + \sum_{j=1}^{seg(1)} x_{1j} + y_2 + \dotsc + \sum_{j=1}^{seg(n-1)} x_{n-1j} + y_n > -c

| where:
| :math:`c` is the battery energy capacity in [kWh]

**Bounds**:

.. math::

    0 \leq x_{ij} \leq p_{ij} \times \Delta t_{ij} \times \eta

| where:
| :math:`p` is the rated power of charger in [kW]
| :math:`\Delta t` is the dwell time in [h]
| :math:`\eta` is the charging efficiency

The optimization is structured to minimize the cost to charge each battery electric
vehicle within defined battery constraints. It is conducted at hourly timescale, meaning
that cost and electricity demand are provided in hourly segments. Charging efficiency is
dependent on the type of electric vehicle supply equipment (EVSE). Efficiency tends to
increase with higher charging rates. The model currently distinguishes between the lower
charging efficiency of AC level 2 charging (90%) and DC charging (95%), where AC
charging is assumed for charging rates at or below 19.2 kW, and DC charging is assumed
for charging rates above 19.2 kW. If a dwell time (:math:`\Delta t`) falls below one
hour, the charge (:math:`x`) available for that segment will be reduced proportional to
the amount of time spent parked (i.e., if a vehicle is parked for 30 minutes, the charge
will be reduced to :math:`1/2`). The default minimum dwell time to consider a charging
event is 0.2 hours, or 12 minutes. This value can be modified depending on the user’s
scenario. The minimum dwell time is set in order to avoid impractical charging events
where, in the real world, a vehicle operator would not plug in their vehicle due to the
shortness of the stop. If the charging rate available is high (e.g., DC Fast Charging),
a shorter minimum dwell time may be warranted. 


Adoption Rate
^^^^^^^^^^^^^
As discussed in :numref:`bev_vmt_projections`, the default BEV adoption rates used in
this model are the VMT projections from NREL’s EFS data.  NREL used their Automotive
Deployment Options Projection Tool (ADOPT) in 2017 to generate the 2018-2050
projections.  Once actual adoption rates become available, those values could be used at
the state and/or UA level to update all remaining VMT projections.  As an example, the
California Energy Commission publishes a dashboard of the Light Duty Vehicle Population
by fuel type (including BEVs) in California for past years.

Similarly, other updates of BEV adoption rate projections at both state and UA levels
undoubtedly will arise over time.  As discussed in the User Manual section above, using
the user interface and modifying the accompanying datasets would allow updated adoption
rate projections to create corresponding BEV charging profiles when desired. Links for
these data sources are available in :numref:`data_sources`. 
