import pandas as pd
import h5py
import os
import numpy as np

parcel_nodes = pd.read_csv(r'C:\Stefan\outputs\parcel_nodes_2018.txt', sep = ' ')

node_index = pd.read_csv(r'C:\Stefan\outputs\node_index_2018.txt', sep = ' ')

origin_node = int(parcel_nodes[parcel_nodes['id'] == 904179]['node_id'])

first_rec = int(node_index[node_index['from_node_id'] == origin_node]['first_rec'])
last_rec = int(node_index[node_index['from_node_id'] == origin_node]['last_rec'])


with h5py.File(os.path.join(r'C:\Stefan\outputs\node_to_node_distance_2018.h5'), "r") as h5file: 
    #max_record = len(h5file['node']) + 1
    node_df = pd.DataFrame(np.asarray(h5file['node'][first_rec:last_rec]), columns = ['node'])
    distance_df = pd.DataFrame(np.asarray(h5file['distance'][first_rec:last_rec]), columns = ['distance'])

d_parcels = parcel_nodes[parcel_nodes['node_id'].isin(node_df['node'])]

o_node = int(parcel_nodes[parcel_nodes['id'] == 904179]['node_id'])

trips = pd.read_csv(r'C:\Stefan\working_estimation_2019\inputs\tripP14.dat', sep = ' ')