import pandas as pd


if __name__ == "__main__":
    bus = pd.read_csv('output/bus.csv')
    zone_load = {}
    for bu in bus.iloc:
        if bu['zone_id'] not in zone_load:
            zone_load[bu['zone_id']] = bu['Pd']
        else:
            zone_load[bu['zone_id']] = zone_load[bu['zone_id']] + bu['Pd']
    print(zone_load)

