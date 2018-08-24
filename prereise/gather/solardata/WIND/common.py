import numpy as np
from pyproj import Proj

def ll2ij(lon_origin, lat_origin, lon, lat):
    """
    Function to find the nearest x/y indices for a given lat/lon using Proj4 projection library

    Parameters
    ----------
    lat : Latitude of coordinate of interest
    lon : Longitude of coordinate of interest

    Results
    -------
    ij  : (x,y) coordinate in the database of the closest pixel to coordinate of interest
    """

    proj_string = """+proj=lcc +lat_1=30 +lat_2=60
                    +lat_0=38.47240422490422 +lon_0=-96.0
                    +x_0=0 +y_0=0 +ellps=sphere
                    +units=m +no_defs"""

    proj2grid = Proj(proj_string)

    origin_xy = proj2grid(lon_origin, lat_origin)
    target_xy = proj2grid(lon, lat)

    delta = np.subtract(target_xy, origin_xy)
    ij = [int(round(x/2000)) for x in delta] # 2km grid resolution

    return tuple(reversed(ij))
