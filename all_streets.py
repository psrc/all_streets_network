

import geopandas as gpd
from geopandas.tools import sjoin
import pandas as pd
from pathlib import Path
import yaml


import osm_split
import osm_extract
import configuration

# todo this is not working (TypeError: expected str, bytes or os.PathLike object, not NoneType)
file = Path().joinpath(configuration.args.configs_dir, "config.yaml")

config = yaml.safe_load(open(file))

# buffer_size = 0.00001


# read shapefiles
# tunnels, bridges, roads = osm_extract.read_road_sf()
print("start reading roads file")
# roads = gpd.read_file(r"OSM_shp\\roads.shp").to_crs(2855)
# print("start reading bridges file")
# bridges = gpd.read_file(r'OSM_shp\\bridges.shp').to_crs(2855)
# print("start reading tunnels file")
# tunnels = gpd.read_file(r'tunnels.shp')

# read in OSM files
if config['download_osm']:
    osm_df = osm_extract.download_osm(config['boundary_file_path'])
    tunnels, bridges, roads = osm_extract.generate_network_topology(osm_df, config['highway_types'])

# go through with the functions in osm_split.py
def exe_split(name, sf, output, buffer_size):
    sf = sf.to_crs(2855)

    print("start splitting tunnels")
    link, no_join, dup = osm_split.split(sf)
    final_link, final_dup = osm_split.join_buffer(sf, no_join, link, buffer_size)

    print(name + "duplicates: ")
    print(final_dup)
    final_link.to_file(output)


exe_split("tunnels", tunnels, config['tunnels_output_file'], config['buffer_size'])
exe_split("bridges", tunnels, config['bridges_output_file'], config['buffer_size'])
exe_split("roads", tunnels, config['roads_output_file'], config['buffer_size'])



