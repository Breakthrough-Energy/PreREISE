from powersimdata.input.grid import Grid
from prereise.gather.winddata.te_wind import te_wind


def test():
    """Prints power output profile of wind farms in Washington state.

    """
    site = te_wind.get_nrel_site(["WA"])

    grid = Grid(["Western"])
    wind_farm = grid.plant.groupby("type").get_group("wind")

    closest_site = te_wind.site2farm(site, wind_farm[["lat", "lon"]])

    start_date = te_wind.pd.Timestamp("2010-01-01")
    end_date = te_wind.pd.Timestamp("2010-01-01 23:55:00")
    date_range = te_wind.pd.date_range(start_date, end_date, freq="5min")

    data = te_wind.get_data(closest_site, date_range)

    [power, _] = te_wind.dict2frame(data, date_range, closest_site)
    profile = te_wind.get_profile(power, wind_farm, closest_site)
    print(profile.head())
    print("Test Done")
