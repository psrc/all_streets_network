import geopandas as gpd
from pathlib import Path
import yaml

import osm_extract
import configuration


file = Path().joinpath(configuration.args.configs_dir, "config.yaml")

config = yaml.safe_load(open(file))


# read in OSM files
if config['download_osm']:
    print("start downloading osm")
    osm_gdf = osm_extract.download_osm(config['boundary_file_path'], config['psrc_buffer_file_path'], config['crs'])

    print("saving extracted osm to directory")
    osm_gdf.to_file(Path(config['output_dir'])/'osm_extract_2285.shp')
    
else:
    print("start reading roads file")
    osm_gdf = gpd.read_file(Path(config['osm_file_path'])).to_crs(config['crs'])


# split downloaded osm network
network_gdf, nodes_gdf = osm_extract.generate_network_topology(osm_gdf, config['highway_types'])
# add ij nodes
# network_gdf = osm_extract.ij_nodes(split_net, config['crs'])

main_network, main_nodes = osm_extract.rm_sub_network(network_gdf, nodes_gdf, config['islands_file_path'])

links, nodes = osm_extract.create_link_node(main_network, main_nodes, config['netbuffer_crs'])

# save results

# network before removing disconnected sub-networks
network_gdf.to_file(Path(config['output_dir'])/'all_split.shp')

# final network
main_network.to_file(Path(config['output_dir'])/'final_network.shp')

# all nodes in the network
main_nodes.to_file(Path(config['output_dir'])/'all_nodes.shp')

# nodes and links for netbuffer
links.to_csv(Path(config['output_dir'])/'links.csv', index=False)
nodes.to_csv(Path(config['output_dir'])/'nodes.csv', index=False)


