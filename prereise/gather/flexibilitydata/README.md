## Bus LSE and Demand Flexibility

| Name            | Grid Model | Methodology  | Dimension    | Notes
|:----------------|:-----------|:-------------|:-------------|:------------|
| Bus LSE data | usa_tamu   | <li>Find the ZIP and FIPS of buses using lat/lon coordinates</li><li>Match with LSE service region according to [1]</li><li>Assign an EIA ID to each bus in the network</li> | 82071*1 | <li>Service region in [1] specified in list of ZIP codes are converted to FIPS</li>
| LSE Flexibility | usa_tamu   | <li>Aggregate the percentage flexibility of all sectors from [2] for each LSE</li><li>Match each LSE with its EIA ID</li> | 8808*828 | <li>Combine with bus LSE data to produce bus-level flexibility</li>

---
**Definition**
* DOE: U.S. Department of Energy
* ERCOT: Electricity Reliability Council of Texas
* EIA: U.S. Energy Information Administration
* LSE: Load Serving Entity
* NREL: National Renewable Energy Laboratory
---

[1] NREL, U.S. Electric Utility Companies and Rates: Look-up by Zipcode (2019) <br> https://data.openei.org/submissions/4042 <br>
[2] Seungwook Ma, Demand Response Across the Continental US for 2006 <br> https://data.openei.org/submissions/180