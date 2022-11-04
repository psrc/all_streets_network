import json
import os
import geopandas as gpd

import numpy as np
from geopandas.tools import sjoin
import shapely.geometry
import geopandas_osm.osm
import geopandas as gpd
import json
from pathlib import Path



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

    print("start splitting tunnels")
    tunnels = osm_df[~osm_df['tunnel'].isnull()]
    tunnels = split_segments(tunnels)

    print("start splitting bridges")
    bridges = osm_df[~osm_df['bridge'].isnull()]
    bridges = split_segments(bridges)

    print("start splitting roads")
    roads = osm_df[osm_df['tunnel'].isnull()]
    roads = roads[roads['bridge'].isnull()]
    roads = split_segments(roads)

    # return tunnels, bridges, roads
    roads = roads.append([tunnels, bridges])
    return roads


def split_segments(gdf, crs=None):
    if not crs:
        crs = gdf.crs

    # create buffer
    gdf_copy = gdf.copy()
    gdf_copy.geometry = gdf_copy.geometry.buffer(0.00001, cap_style=2)  # flat buffer

    # assign road ID
    road_id = [j for j in range(len(gdf_copy))]
    gdf_copy["road_id"] = road_id

    # splitting
    un = gdf.geometry.unary_union
    geom = [i for i in un]
    id = [j for j in range(len(geom))]
    # split links with link ID
    unary = gpd.GeoDataFrame({"link_id": id, "geometry": geom}, crs=crs)

    # merge split links with original roads to keep attributes
    result = sjoin(unary, gdf_copy, how="left", op='within')

    # all links that are not joined back to the original roads
    print("links that are not joined back to the original roads")
    print(result[result['road_id'].isnull()])
    # link_no_join = result[result['road_id'].isnull()]

    # find list of all links that are duplicated in the process (because some roads are overlapping)
    print("list of all links that are duplicated in the process")
    print(result[result["link_id"].duplicated()]["link_id"].values.tolist())
    # link_dup = result[result["link_id"].duplicated()]["link_id"].values.tolist()

    return result


def ij_nodes(gdf):

    # find union of all starting points
    # coord[0]: starting points of lines, coord[-1]: ending points of lines
    # coord[0][0]: x coordinates, coord[0][1]: y coordinates
    points_x = np.sort(np.unique(np.append(np.array(gdf['geometry'].apply(lambda x: x.coords[0][0])),
                                           np.array(gdf['geometry'].apply(lambda x: x.coords[-1][0])))))
    points_y = np.sort(np.unique(np.append(np.array(gdf['geometry'].apply(lambda x: x.coords[0][1])),
                                           np.array(gdf['geometry'].apply(lambda x: x.coords[-1][1])))))

    # i and j nodes
    points_x = dict(enumerate(points_x, 1))
    points_y = dict(enumerate(points_y, 1))
    points_x = dict([(value, key) for key, value in points_x.items()])
    points_y = dict([(value, key) for key, value in points_y.items()])

    gdf["i_node"] = gdf["geometry"].apply(lambda x: str(points_x[x.coords[0][0]]) + '-' + str(points_y[x.coords[0][1]]))
    gdf["j_node"] = gdf["geometry"].apply(lambda x: str(points_x[x.coords[-1][0]]) + '-' + str(points_y[x.coords[-1][1]]))

    return gdf

