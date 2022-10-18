import geopandas as gpd
import networkx as nx
import pandas as pd
import numpy as np
from scipy.spatial import cKDTree
import time
import h5py
import os

output_dir = r'C:\Stefan\outputs\2014'

with h5py.File(os.path.join(output_dir, 'node_to_node_distance_2014.h5'), "r") as h5file: 
    max_record = len(h5file['node']) + 1
    node_df = pd.DataFrame(np.asarray(h5file['node'][0:max_record]), columns = ['node'])
    distance_df = pd.DataFrame(np.asarray(h5file['distance'][0:max_record]), columns = ['distance'])


node_index = pd.read_csv(os.path.join(output_dir, 'node_index_2014.txt'), sep = ' ')
recode = pd.DataFrame(node_index['from_node_id'].unique(), columns=['node_id'])
recode['new_node_id'] = recode.index + 1
node_index = node_index.merge(recode, left_on = 'from_node_id', right_on = 'node_id')
node_index['from_node_id'] =  node_index['new_node_id']
node_index = node_index[['from_node_id', 'first_rec', 'last_rec']]
node_index.to_csv(os.path.join(output_dir, 'node_index_2018.txt'), sep = ' ', index = False)

recode_dict = dict(zip(recode['node_id'],recode['new_node_id']))
parcel_nodes = pd.read_csv(os.path.join(output_dir, 'parcel_nodes_2014.txt'), sep = ' ')
parcel_nodes['node_id'] = parcel_nodes['node_id'].map(recode_dict)  
parcel_nodes['node_id'] = parcel_nodes['node_id'].fillna(0)
parcel_nodes['node_id'] = parcel_nodes['node_id'].astype('int32')
parcel_nodes.to_csv(os.path.join(output_dir, 'parcel_nodes_2018.txt'), sep = ' ', index = False)

#recode_dict = dict(zip(recode['node_id'],recode['new_node_id']))
node_df['node'] = node_df['node'].map(recode_dict)   
node_df['node'] = node_df['node'].astype('int32')


#new_node_array = np.vectorize(recode_dict.get)(node_array)
#u,inv = np.unique(node_array,return_inverse = True)
#new_node_array = np.array([recode_dict[x] for x in node_array])

#df = pd.DataFrame([new_node_array, distance_array])


with h5py.File(os.path.join(output_dir, 'node_to_node_distance_2018.h5'), 'w') as h5file:
    h5file.create_dataset('node', node_df['node'].astype('int32'), compression='gzip')
    h5file.create_dataset('distance', distance_df['distance'].astype('int16'), compression='gzip')

    