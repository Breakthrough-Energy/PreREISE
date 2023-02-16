Capabilities and Data
#####################
The transportation electrification module calculates an estimate of the additional
hourly electricity demand from the electrification of transportation vehicles for all
U.S. urban and rural areas for years ranging from 2017-2050.  The hourly estimation
builds upon data collected representing over half a million driving events.

Additional data sets allow for profiles to be generated across the following dimensions:

+ 4 vehicle types (LDV, LDT, MDV, and HDV)
+ 34 simulation years (2017-2050)
+ 481 Urban Areas (as defined by the U.S. Census Bureau) and 48 Rural Areas (one for
  each continental U.S. State).

The charging of each vehicle is currently simulated via one of two methods: Immediate
Charging and Smart Charging.Immediate Charging simulates charging occurring from the
time the vehicle plugs in until either the battery is full or until the vehicle departs
on the next trip. An example profile is in orange below, added on top of an example
of non-transportation base demand (:numref:`example_ldv_immediate_load`).  

.. _example_ldv_immediate_load:

.. figure:: demand/transportation_electrification/img/data/ldv_immediate_load.png
   :align: center

   Example of BEV Immediate Charging stacked on top of non-transportation base demand

Smart Charging refers to coordinated charging between drivers (either in aggregate or
individually) and utilities or balancing authorities in response to a user-adjustable
objective function. The example profile below (:numref:`example_ldv_smart_load`) 
provides the same amount of charging energy to the same set of vehicles in the Immediate 
Charging figure above (:numref:`example_ldv_immediate_load`). This instance of Smart 
Charging manages the peak demand of the non-transportation base demand plus the 
additional transportation electrification load to be substantially lower.  

.. _example_ldv_smart_load:

.. figure:: demand/transportation_electrification/img/data/ldv_smart_load.png
   :align: center

   Example of BEV Smart Charging “filling in the Valleys” of non-transportation base demand
