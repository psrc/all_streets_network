

from wsgiref.util import shift_path_info
import geopandas as gpd
from geopandas.tools import sjoin
import pandas as pd
from pathlib import Path
import yaml

import osm_extract
import configuration


file = Path().joinpath(configuration.args.configs_dir, "config.yaml")

config = yaml.safe_load(open(file))


# read in OSM files
if config['download_osm']:
    print("start downloading osm")
    osm_gdf = osm_extract.download_osm(config['boundary_file_path'], config['crs'])
    
else:
    print("start reading roads file")
    osm_gdf = gpd.read_file(Path(config['output_dir'])/'osm_extract.shp')

# split downloaded osm network
split_net = osm_extract.generate_network_topology(osm_gdf, config['highway_types'])
# add ij nodes
split_net = osm_extract.ij_nodes(split_net)


# save network
# osm_extract.gdf_to_shapefile(split_net, config['output_dir'], 'all_split.shp')
split_net.to_file(Path(config['output_dir'])/'all_split3.shp')




