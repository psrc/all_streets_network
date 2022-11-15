

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

    print("saving extracted osm to directory")
    osm_gdf.to_file(Path(config['output_dir'])/'osm_extract_2285.shp')
    
else:
    print("start reading roads file")
    osm_gdf = gpd.read_file(Path(config['osm_file_path'])).to_crs(config['crs'])


# split downloaded osm network
split_net = osm_extract.generate_network_topology(osm_gdf, config['highway_types'])
# add ij nodes
network, all_nodes = osm_extract.ij_nodes(split_net)

main_network = osm_extract.rm_sub_network(network, config['islands_file_path'], config['crs'])


# save results

# network before removing disconnected sub-networks
# network.to_file(Path(config['output_dir'])/'all_split.shp')

# final network
main_network.to_file(Path(config['output_dir'])/'final_network.shp')

# list of all nodes in the network
all_nodes.to_file(Path(config['output_dir'])/'all_nodes.shp')



