Eastern
#######
The construction of the Eastern Interconnection demand profile is slightly different
from the Western counterpart. We still download historical demand data from EIA
and perform the 3-step data processing/cleaning as for the Western Interconnection
for all Balancing Authorities (BAs) but MISO (Midcontinent Independent System Operator)
and SPP (Southwest Power Pool).

MISO and SPP operate across multiple U.S. states (e.g. 15 for MISO) and cover several
load zones in our grid model. Instead of considering a single hourly profile shape for
each entity and having load zones sharing the exact same profile in different part of
the country, we further split MISO and SPP into subareas. The hourly subarea demand
profiles for MISO and SPP can be downloaded on their respective website (check `SPP
hourly load`_ and `MISO hourly load`_). The geographical definitions of these subareas
are obtained directly from contact at the BAs via either customer service or internal
request management system (see the `RMS`_ for SPP). Given the geographical definitions,
i.e., list of counties for each subarea, each bus within MISO and SPP is mapped to the
subarea it belongs to.

The overall procedure is is demonstrated in the `eastern demand notebook`_.


.. _SPP hourly load: https://marketplace.spp.org/pages/hourly-load
.. _MISO hourly load: https://www.misoenergy.org/markets-and-operations/real-time--market-data/market-reports#nt=%2FMarketReportType%3ASummary%2FMarketReportName%3AHistorical%20Daily%20Forecast%20and%20Actual%20Load%20by%20Local%20Resource%20Zone%20(xls)&t=10&p=0&s=MarketReportPublished&sd=desc
.. _RMS: https://spprms.issuetrak.com/Login.asp
.. _eastern demand notebook: https://github.com/Breakthrough-Energy/PreREISE/blob/develop/prereise/gather/demanddata/eia/demo/eastern_demand_v6_demo/eastern_demand_v6_demo.ipynb
