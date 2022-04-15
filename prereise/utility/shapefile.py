import os
import urllib


# Mostly copied from download_states_shapefile in postreise.plot.plot_states
def download_shapefiles(url_base, shape_filename, base_filepath, overwrite=False):
    """Downloads shapefiles from url and writes them to a local folder.

    :param str url_base: URL to folder containing shapefiles. Must include foward slash at end.
    :param str shape_filename: all shapefiles in folder must have the same name
    :param str base_filepath: folder to save files
    :param bool overwrite: Whether to overwrite existing files, defaults to False
    :return: (*str*)  -- path to shapefile
    """
    os.makedirs(base_filepath, exist_ok=True)
    shape_entensions = ["cpg", "dbf", "prj", "shp", "shx"]

    for ext in shape_entensions:
        filepath = os.path.join(base_filepath, f"{shape_filename}.{ext}")

        if not os.path.isfile(filepath) or overwrite:
            response = urllib.request.urlopen(f"{url_base}{shape_filename}.{ext}")

            with open(filepath, "wb") as f:
                f.write(response.read())
        else:
            print(f"Skipping {filepath} because it already exists.")

    filename = os.path.join(base_filepath, f"{shape_filename}.shp")
    return filename
