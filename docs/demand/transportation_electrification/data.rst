Capabilities and Data
#####################
The transportation electrification module calculates an estimate of the additional hourly electricity demand from the electrification of transportation vehicles for all U.S. urban and rural areas for years ranging from 2017-2050.  The hourly estimation builds upon data collected representing over half a million driving events. 

Additional data sets allow for profiles to be generated across the following
dimensions: 

+ 4 vehicle types (light-duty vehicles (LDV), light-duty trucks (LDT), medium-duty
  vehicles (MDV), and heavy-duty vehicles (HDV)) 
+ 33 simulation years (2017-2050) 
+ 481 Urban Areas (as defined by the U.S. Census Bureau) and 50 Rural Areas (one for
  each U.S. State). 

The charging of each vehicle is currently simulated via one of two methods: Immediate
Charging and Smart Charging.  Immediate Charging simulates charging occurring from the
time the vehicle plugs in until either the battery is full or until the vehicle departs
on the next trip.  An example profile is in orange below, added on top of the base load
demand (:numref:`example_ldv_immediate_load`).  

.. _example_ldv_immediate_load:

.. figure:: demand/transportation_electrification/img/data/ldv_immediate_load.png
   :align: center

   Example of LDV Immediate Charging Stacked on Top of Base Load (3 Weeks)

Smart Charging refers to coordinated charging in response to a user-adjustable
objective function.  The example profile below (:numref:`example_ldv_smart_load`)
provides the same amount of charging to the same set of vehicles in the Immediate
Charging figure above (:numref:`example_ldv_immediate_load`).  This instance of Smart
Charging manages the peak demand of the base load plus the additional transportation
electrification load to be substantially lower (~50GW vs ~40GW in this example case).  

.. _example_ldv_smart_load:

.. figure:: demand/transportation_electrification/img/data/ldv_smart_load.png
   :align: center

   Example of LDV Smart Charging “Filling in the Valleys” of Base Load (3 Weeks)
