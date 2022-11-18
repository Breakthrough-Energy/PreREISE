## Architecture Diagram

``` mermaid
graph TD
    A[Vehicle Demand Interface Function] -->|choose vehicle type, vehicle range, model year, charging strategy| B(Load Data)
    I --> |evaluate whether charging is available| C{calculate charging over \n given trip window} 
    J --> H[Geospecific Hourly Load Profile]
    H --> F[fa:fa-car Vehicle Demand Profiles]
    H --> E[Vehicle Load Plots]
    H --> G[Vehicle Load Statistics]
    B --> |parse out relevant columns| I[Charging availability and strategy]

    subgraph Trip___Window Loop
        C --> D(Normalized Trip Demand)
        D --> |scale for daily/monthly driving patterns, yearly regional scaling factors| J(Scaled Trip Demand)
        C --> |loop over days in year| C
    end
```