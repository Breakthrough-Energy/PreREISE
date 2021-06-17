from getpass import getpass

from powersimdata.input.grid import Grid

from prereise.gather.solardata.helpers import to_reise
from prereise.gather.solardata.nsrdb import sam

print("solar data nsrdb_sam population")
electricity_grid = Grid("USA")

solar_farm = electricity_grid.plant.groupby("type").get_group("solar")


# key = getpass(prompt='api_key=')
key = "1x3MR1XhGQYH8hsPgJr4SvhT3wRm96krTll9ir1z"
email = "lfan8@uh.edu"
solar_farm_data = sam.retrieve_data(solar_farm, email, key, year="2016")

solar_farm_data = to_reise(solar_farm_data)
solar_farm_data.to_csv("solar.csv")
print("solar data nsrdb_sam population end")
