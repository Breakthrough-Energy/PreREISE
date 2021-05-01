from powersimdata.input.grid import Grid
#from powersimdata.network.usa_tamu.usa_tamu_model import area_to_loadzone
from prereise.gather.hydrodata.eia.interpolate_capacity_factors import get_profile
import pandas as pd

print("start hydro data population")

electricity_grid = Grid('USA')
hydro_plant = electricity_grid.plant.groupby('type').get_group('hydro')
print(type(hydro_plant))
hydro_plant_data = get_profile(hydro_plant,start=pd.Timestamp(2016, 1, 1), end=pd.Timestamp(2016, 1, 1, 23))

hydro_plant_data.to_csv('hydro.csv')

print("end hydro data population")

