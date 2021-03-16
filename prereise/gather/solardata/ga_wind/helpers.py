import numpy as np

proj_string = (
    "+proj=lcc +lat_1=30 +lat_2=60"
    " +lat_0=38.47240422490422 +lon_0=-96.0"
    " +x_0=0 +y_0=0 +ellps=sphere"
    " +units=m +no_defs"
)


def ll2ij(transformer, lon_origin, lat_origin, lon, lat):
    """Finds nearest x/y indices for a given lat/lon.

    :param pyproj.transformer.Transformer: transformer object used for reprojection.
    :param float lat_origin: latitude of coordinate of origin.
    :param float lon_origin: longitude of coordinate of origin.
    :param float lat: latitude of coordinate of interest.
    :param float lon: longitude of coordinate of interest.
    :return: (*tuple*) -- coordinate of the closest pixel in the database.
    """

    origin_xy = transformer.transform(lon_origin, lat_origin)
    target_xy = transformer.transform(lon, lat)

    delta = np.subtract(target_xy, origin_xy)

    # 2-km grid resolution
    ij = [int(round(x / 2000)) for x in delta]

    return tuple(reversed(ij))
