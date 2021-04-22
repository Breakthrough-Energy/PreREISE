from powersimdata.input.grid import Grid
from prereise.gather.winddata.rap import rap, impute, helpers

print("wind data population")
electricity_grid = Grid("Texas")

wind_farm = electricity_grid.plant.groupby("type").get_group("wind")
wind_farm_data, wind_farm_data_missing = rap.retrieve_data(wind_farm, start_date='2021-01-01', end_date='2021-03-31')
impute.gaussian(wind_farm_data, wind_farm,inplace = True)
wind_farm_data_reise = helpers.to_reise(wind_farm_data)
wind_farm_data_reise.to_csv('wind.csv')
print("wind data population end")
