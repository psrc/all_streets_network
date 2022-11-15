import json
import os

import numpy as np
import pandas as pd
from geopandas.tools import sjoin
import shapely.geometry
import geopandas_osm.osm
import geopandas as gpd
import json
from pathlib import Path
import networkx as nx


def download_osm(boundary_file, crs):
    with open(boundary_file) as f:
        data = json.load(f)

    poly = shapely.geometry.shape(data['features'][0]['geometry'])

    gdf = geopandas_osm.osm.query_osm('way', poly, recurse='down', tags='highway')
    gdf = gdf[gdf.type == 'LineString'][['highway', 'name', 'geometry', 'bridge', 'tunnel', 'oneway']]
    gdf = gdf.to_crs(crs)
    return gdf


def gdf_to_shapefile(gdf, file_path, file_name):
    file_path = Path(file_path)
    gdf.to_file(file_path / file_name)


def generate_network_topology(osm_df, highway_types):
    # all_roads = osm_df[osm_df.type == 'LineString'][['highway', 'name', 'geometry', 'bridge', 'tunnel', 'oneway']]
    osm_df = osm_df[osm_df['highway'].isin(highway_types)]

    road_id = [j + 1 for j in range(len(osm_df))]
    osm_df["road_id"] = road_id

    print("start splitting tunnels")
    tunnels = osm_df[~osm_df['tunnel'].isnull()]
    tunnels = split_segments(tunnels, 't')

    print("start splitting bridges")
    bridges = osm_df[~osm_df['bridge'].isnull()]
    bridges = split_segments(bridges, 'b')

    print("start splitting roads")
    roads = osm_df[osm_df['tunnel'].isnull()]
    roads = roads[roads['bridge'].isnull()]
    roads = split_segments(roads, 'r')

    # return tunnels, bridges, roads
    roads = roads.append([tunnels, bridges])

    roads = roads.sort_values(by=['id'])
    roads['link_id'] = [j + 1 for j in range(len(roads))]

    return roads


def split_segments(gdf, link_letter, crs=None):
    if not crs:
        crs = gdf.crs

    # create buffer
    gdf_copy = gdf.copy()
    gdf_copy.geometry = gdf_copy.geometry.buffer(0.00001)  # flat buffer: , cap_style=2

    # assign road ID
    # road_id = [j for j in range(len(gdf_copy))]
    # gdf_copy["road_id"] = road_id

    # splitting
    un = gdf.geometry.unary_union
    geom = [i for i in un]
    id = [link_letter + '-' + str(j + 1) for j in range(len(geom))]

    # split links with link ID
    unary = gpd.GeoDataFrame({"id": id, "geometry": geom}, crs=crs)

    # merge split links with original roads to keep attributes
    result = sjoin(unary, gdf_copy, how="left", op='within')
    result = result.drop(columns=['index_right'])

    # all links that are not joined back to the original roads
    print("links that are not joined back to the original roads")
    print(result[result['road_id'].isnull()])
    # link_no_join = result[result['road_id'].isnull()]

    # find list of all links that are duplicated in the process (because some roads are overlapping)
    print("list of all links that are duplicated in the process")
    print(result[result["id"].duplicated()]["id"].values.tolist())
    # link_dup = result[result["id"].duplicated()]["id"].values.tolist()

    return result


def ij_nodes(gdf):
    gdf_ij = gdf.copy()

    # find all unique points
    # coord[0]: starting points of lines, coord[-1]: ending points of lines
    gdf_ij['points_start'] = gdf_ij['geometry'].apply(lambda x: x.coords[0])
    gdf_ij['points_end'] = gdf_ij['geometry'].apply(lambda x: x.coords[-1])

    points = list(set(gdf_ij['points_start'].values.tolist() + gdf_ij['points_end'].values.tolist()))
    nodes_dict = dict(enumerate(points, 1))
    nodes_dict = dict([(value, key) for key, value in nodes_dict.items()])

    gdf_ij["i_node"] = gdf_ij['points_start'].apply(lambda x: str(nodes_dict[x]))
    gdf_ij["j_node"] = gdf_ij['points_end'].apply(lambda x: str(nodes_dict[x]))
    gdf_ij = gdf_ij.drop(columns=['points_start', 'points_end'])

    # create a gdf for all nodes
    df_nodes = pd.DataFrame({'node_id': nodes_dict.values(),
                             'coords': nodes_dict.keys()})
    df_nodes['geom_x'] = df_nodes['coords'].apply(lambda x: x[0])
    df_nodes['geom_y'] = df_nodes['coords'].apply(lambda x: x[1])
    gdf_nodes = gpd.GeoDataFrame(df_nodes, geometry=gpd.points_from_xy(df_nodes['geom_x'], df_nodes['geom_y'])).drop(
        columns=['coords', 'geom_x', 'geom_y'])

    return gdf_ij, gdf_nodes

# to remove disconnected sub-networks that are not on islands
def rm_sub_network(gdf, islands, crs):
    x_graph = nx.Graph()
    graph = nx.from_pandas_edgelist(gdf, 'i_node', 'j_node',
                                    ['id', 'geometry', 'highway', 'name', 'bridge', 'tunnel', 'oneway', 'road_id',
                                     'link_id', 'i_node', 'j_node'], x_graph)
    # find all sub_networks
    sep_graph = [graph.subgraph(c).copy() for c in sorted(nx.connected_components(graph), key=len, reverse=True)]

    # combine all edges other than the main network
    df_list = []
    for i in range(1, len(sep_graph)):
        df = nx.to_pandas_edgelist(sep_graph[i])
        df_list.append(df)
    all_disconnected = pd.concat(df_list, ignore_index=True)

    # create a gdf out of the disconnected network and clip with island shp
    gdf_disconnect = gpd.GeoDataFrame(all_disconnected, geometry='geometry').set_crs(crs)

    # keep only networks on islands: clip disconnected networks using islands
    islands = gpd.read_file(Path(islands)).to_crs(crs)
    island_network = gpd.clip(gdf_disconnect, islands)

    # gdf of main network
    df_final_network = nx.to_pandas_edgelist(sep_graph[0]).append(island_network)
    final_network = gpd.GeoDataFrame(df_final_network, geometry='geometry').set_crs(crs)

    return final_network
