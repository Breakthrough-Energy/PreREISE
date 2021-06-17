# from getpass import getpass

from powersimdata.input.grid import Grid

from prereise.gather.solardata.ga_wind import ga_wind
from prereise.gather.solardata.helpers import to_reise

print("solar data population")
electricity_grid = Grid("Texas")

solar_farm = electricity_grid.plant.groupby("type").get_group("solar")


# key = getpass(prompt='api_key=')
key = "1x3MR1XhGQYH8hsPgJr4SvhT3wRm96krTll9ir1z"
solar_farm_data = ga_wind.retrieve_data(
    solar_farm, key, start_date="2016-01-01", end_date="2016-01-15"
)

solar_farm_data = to_reise(solar_farm_data)
solar_farm_data.to_csv("solar.csv")
print("solar data population end")
