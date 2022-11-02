import json
import os
import geopandas as gpd
from geopandas.tools import sjoin
import shapely.geometry
import geopandas_osm.osm
import geopandas as gpd 
import json
from pathlib import Path

from osm_split import split

def download_osm(boundary_file, crs):
    # boundary = gpd.read_file(r'W:\gis\projects\OSM\boundary3.shp')
    # boundary.to_file(r'W:\gis\projects\OSM\boundary3.geojson', driver='GeoJSON')

    # highway_types = ['trunk', 'trunk_link', 'motorway', 'motorway_link', 
    # 'primary', 'primary_link', 'residential', 'road', 'secondary', 
    # 'service', 'tertiary', 'tertiary_link', 'secondary_link', 
    # 'cycleway', 'footway', 'pedestrian', 'living_street', 'unclassified', 
    # 'steps']


    with open(r'W:\gis\projects\OSM\boundary3.geojson') as f:
        data = json.load(f)

    poly = shapely.geometry.shape(data['features'][0]['geometry'])
    
    gdf = geopandas_osm.osm.query_osm('way', poly, recurse='down', tags='highway')
    gdf = gdf[gdf.type == 'LineString'][['highway', 'name', 'geometry', 'bridge', 'tunnel', 'oneway']]
    gdf = gdf.to_crs(crs)
    return gdf


def gdf_to_shapefile(gdf, file_path, file_name):
    file_path = Path(file_path)
    gdf.to_file(file_path/file_name)

def generate_network_topology(osm_df, highway_types):
    #all_roads = osm_df[osm_df.type == 'LineString'][['highway', 'name', 'geometry', 'bridge', 'tunnel', 'oneway']]
    osm_df = osm_df[osm_df['highway'].isin(highway_types)]

    tunnels = osm_df[~osm_df['tunnel'].isnull()]
    tunnels = split_segments(tunnels)

    bridges = osm_df[~osm_df['bridge'].isnull()]
    bridges = split_segments(bridges)

    roads = osm_df[osm_df['tunnel'].isnull()]
    roads = roads[roads['bridge'].isnull()]
    roads = split_segments(roads)

    #return tunnels, bridges, roads
    # roads = roads.append([tunnels, bridges])
    return roads, tunnels, bridges

def split_segments(gdf, crs=None):
    if not crs:
        crs = gdf.crs

    print("start splitting tunnels")
    gdf_copy = gdf.copy()
    gdf_copy.geometry = gdf_copy.geometry.buffer(0.00001)
    #link, no_join, dup = osm_split.split(sf)
    un = gdf.geometry.unary_union
    geom = [i for i in un]
    id = [j for j in range(len(geom))]
    unary = gpd.GeoDataFrame({"id":id,"geometry":geom}, crs = crs)
    result =sjoin(unary, gdf_copy, how="inner",op='within')
    return result

    # road_id = [j for j in range(len(osm_split))]
    # osm_split["road_id"] = road_id

    # geom = [i for i in osm_split.geometry.unary_union]
    # id = [j for j in range(len(geom))]
    # unary = gpd.GeoDataFrame({"link_id":id,"geometry":geom}, crs="EPSG:2855")
    # # join links back to roads to give them properties
    # result =sjoin(unary, osm_split, how="left",op='within')

    # # all links that are not joined back to the original roads
    # link_no_join = result[result['road_id'].isnull()]

    # # find list of all links that are duplicated in the process (because some roads are overlapping)
    # link_dup = result[result["link_id"].duplicated()]["link_id"].values.tolist()

    # return result, link_no_join, link_dup


# secondary results for links that did not join back to road in the initial results (join with buffer)
def join_buffer(split_sf, link_no_join, result, buffer_size):
    
    # create buffer with original shapefile
    sf_buf = split_sf.copy()
    sf_buf.geometry = sf_buf.geometry.buffer(buffer_size,cap_style=2) # flat buffer

    # join the links to the buffered roads
    result_buf = gpd.sjoin(link_no_join[["link_id","geometry"]], sf_buf, how="left", op="within")

    # combine the 2 results: original split (without those not successfully joined) + links joined with buffer
    result_links = result[~result['road_id'].isnull()].append(result_buf)
    result_links = result_links[["link_id", "road_id", "highway", "name",	"bridge", "tunnel", "oneway", "geometry"]].astype({"road_id": int})

    # find list of all links that are duplicated in the process
    link_dup = result_links[result_links["link_id"].duplicated()]["link_id"].values.tolist()

    return result_links, link_dup





# roads.to_file(r'C:\Stefan\OSM\roads.shp')
# bridges.to_file(r'C:\Stefan\OSM\bridges.shp')
# tunnels.to_file(r'C:\Stefan\OSM\tunnels.shp')


