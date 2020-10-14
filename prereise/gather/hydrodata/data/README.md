# Hydroelectric Data Used to Generate Profiles

The general methodology is described in the following publication: [U.S. Test System with High Spatial and Temporal Resolution for Renewable Integration Studies][IEEE]. The file here have been produced as follows:
* **texas_hydro_generation.csv**:
Data have been collected on the [ERCOT] website. The *Fuel Mix Report 2007 - 2019* reports actual generation by fuel type for each 15 minute settlement interval, as well as totals by month and year. The time zone is assumed to be Central Time, so this was converted to GMT (CST is GMT-6).
* **western_hydro_generation.csv**:
The [U.S. Army Corps of Engineers’ Northwestern hydro system][Army Corps] is used to obtain a generic hydro profile to be applied to the generators in the Western Interconnection, with the exception of Wyoming and California (see publication and notebook for more details). Also, we obtain additional information on dams' coordinates and capacity in [Wikipedia]. We noticed outliers for two dams: WAN and PRD where the power output on 4/26/2019 16:00 UTC exceeds their respective capacity. These outliers were replaced with an average of the hour before and after the outlier hour, for each of the two dams.
* **usa_hydro_capacity_factors.csv**:
Monthly capacity factors for hydro plant across the country are reported by EIA [here][Capacity Factors] and can be used to generate a unique hydro profile by interpolating the monthly data. The derived hourly profile can be used to generate a profile for each plant. This was used to generate our first hydro profile version.

[IEEE]: https://arxiv.org/abs/2002.06155
[ERCOT]: http://www.ercot.com/gridinfo/generation/
[Army Corps]: http://www.nwd-wc.usace.army.mil/dd/common/dataquery/www/
[Wikipedia]: https://en.wikipedia.org/wiki/List_of_dams_in_the_Columbia_River_watershed
[Capacity Factors]: https://www.eia.gov/electricity/annual/html/epa_04_08_b.html
