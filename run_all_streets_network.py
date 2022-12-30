import configuration
import geopandas as gpd
from pathlib import Path
import yaml

import all_streets
import run_netbuffer

file = Path().joinpath(configuration.args.configs_dir, "config.yaml")

config = yaml.safe_load(open(file))

# create links and nodes input for netbuffer
links, nodes = all_streets.create_all_streets_network(config)

# nodes and links for netbuffer
# print("save nodes and links for netbuffer")
links.to_csv('./data/links.csv', index=False)
nodes.to_csv('./data/nodes.csv', index=False)

# run netbuffer
run_netbuffer.run()

