import geopandas as gpd
import networkx as nx
import pandas as pd
import numpy as np
from scipy.spatial import cKDTree
import time
import h5py
import os

# input files
links = gpd.read_file(r'C:\Stefan\inputs\all_merge_clip_no_service_footway.shp')
#parcels = gpd.read_file(r'C:\Stefan\inputs\parcel_point_2018.shp')
my_crs = links.crs
subnet_max = 12

#output directory
output_dir = r'C:\Stefan\outputs'

chunk_size = 1000

# add i & j node IDs to links & create node file 
links['from'] = links['from_x'].astype(str) + '-' + links['from_y'].astype(str)
links['to'] = links['to_x'].astype(str) + '-' + links['to_y'].astype(str)
nodes = links.groupby('from')['from_x', 'from_y'].first()
nodes2 = links.groupby('to')['to_x', 'to_y'].first()
x = nodes['from_x'].tolist() + nodes2['to_x'].tolist()
y = nodes['from_y'].tolist() + nodes2['to_y'].tolist()
d = {'x' : x, 'y' : y}
nodes_df = pd.DataFrame(d)
nodes_df = nodes_df.drop_duplicates()
nodes_df['node_id'] = nodes_df.index 

links['from_node_id'] = 0
links['to_node_id'] = 0
link_cols = links.columns
links = links.merge(nodes_df, how = 'left', left_on = ['from_x', 'from_y'], right_on = ['x', 'y'])
links['from_node_id'] = links['node_id']
links = links[link_cols]
links = links.merge(nodes_df, how = 'left', left_on = ['to_x', 'to_y'], right_on = ['x', 'y'])
links['to_node_id'] = links['node_id']
links = links[link_cols]
links['edge_id'] = links['OBJECTID']

# only keep connected netowork. 
x = nx.Graph()
G = nx.from_pandas_edgelist(links, 'from_node_id', 'to_node_id', ['Shape_Leng', 'edge_id', 'from_node_id', 'to_node_id'], x)
S = [G.subgraph(c).copy() for c in sorted(nx.connected_components(G), key=len, reverse=True)]

# need to look at these subnets in GIS to see which ones to keep (puges sound islands --> some disconnected network)
df_list = []
for i in range (0, subnet_max):
    if i in [0, 1, 2, 3, 4, 7]:
        df = nx.to_pandas_edgelist(S[i])
        connected_links = links[links['edge_id'].isin(df['edge_id'])]
        #connected_links.to_file(r'C:\Stefan\OSM\connected_links_%s.shp' % (str(i)))
        df_list.append(df)

# merge the subnets
links2 = pd.concat(df_list)
links = links[links['edge_id'].isin(links2['edge_id'])]
links['name'] = 'main street'
links['direction'] = 0
links['speed_limit_in_mph'] = 25
links['link_type'] = 3
links['lane_capacity_in_vhc_per_hour'] = 2000
links['link_id'] = links['edge_id']
links['number_of_lanes'] = 2
links['length_in_mile'] = links['Shape_Leng'] / 5280

links.to_file(os.path.join(output_dir, 'input_links.shp'))

links = links[['name', 'from_node_id', 'to_node_id', 'direction', 'speed_limit_in_mph', 'link_type', 'lane_capacity_in_vhc_per_hour', 'link_id','number_of_lanes', 'length_in_mile']]

#links = pd.DataFrame(links)
links.to_csv(os.path.join(output_dir, 'input_link.csv'), index = False)

node_list = list(set(links['from_node_id'].tolist() + links['to_node_id'].tolist()))
nodes_df = nodes_df[nodes_df['node_id'].isin(node_list)]
nodes_gdf = gpd.GeoDataFrame(nodes_df, geometry=gpd.points_from_xy(nodes_df.x, nodes_df.y))
nodes_gdf.crs = my_crs 

nodes_gdf.to_file(os.path.join(output_dir, 'input_node.shp'))
nodes_df = nodes_df[['node_id', 'x', 'y']]
nodes_df.to_csv(os.path.join(output_dir, 'input_node.csv'), index = False)

# def to find the nearest node to a poi (parcel) on the network
# def ckdnearest(gdA, gdB, acol, bcol):   
#     nA = np.array(list(zip(gdA.geometry.x, gdA.geometry.y)) )
#     nB = np.array(list(zip(gdB.geometry.x, gdB.geometry.y)) )
#     btree = cKDTree(nB)
#     dist, idx = btree.query(nA,k=1)
#     #res = gdB.iloc[idx][bcol].values
#     df = pd.DataFrame.from_dict({'distance': dist.astype(int), acol : gdA[acol].values, bcol : gdB.iloc[idx][bcol].values})
#     return df

# closest_node = ckdnearest(parcels, nodes_gdf, 'parcel_id', 'node_id')
# # prepare node file
# nodes_df = nodes_df[nodes_df['node_id'].isin(closest_node.node_id)]
# nodes_df = nodes_df[['node_id', 'x', 'y']]
# nodes_df['x'] = nodes_df['x'].astype(int)
# nodes_df['y'] = nodes_df['y'].astype(int)

# nodes_df.to_csv(os.path.join(output_dir, 'psrc_2018_nodes.csv'), index = False)

# add nearest node_id to parcel file

#parcels = parcels.merge(closest_node, how = 'left', left_on = 'parcel_id', right_on = 'parcel_id')







#parcel node file:
#parcels = parcels.rename(columns = {'id' : 'node_id'})
# parcels = parcels.rename(columns = {'parcel_id' : 'id'})
# parcels = parcels[['id', 'node_id']]
# parcels['node_id'] = parcels['node_id'].astype('int32')
# parcels['id'] = parcels['id'].astype('int64')
# parcels.to_csv(os.path.join(output_dir, 'parcel_nodes_2018.txt'), sep = ' ', index = False)
