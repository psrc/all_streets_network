import json

import shapely.geometry
import geopandas_osm.osm
import geopandas as gpd 
import json

def download_osm(boundary_file):
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
    
    return(geopandas_osm.osm.query_osm('way', poly, recurse='down', tags='highway'))

    

def generate_network_topology(osm_df, highway_types):
    all_roads = osm_df[osm_df.type == 'LineString'][['highway', 'name', 'geometry', 'bridge', 'tunnel', 'oneway']]
    all_roads = all_roads[all_roads['highway'].isin(highway_types)]

    tunnels = all_roads[~all_roads['tunnel'].isnull()].to_crs(2855)
    bridges = all_roads[~all_roads['bridge'].isnull()].to_crs(2855)

    roads = all_roads[all_roads['tunnel'].isnull()]
    roads = roads[roads['bridge'].isnull()].to_crs(2855)

    return tunnels, bridges, roads





# roads.to_file(r'C:\Stefan\OSM\roads.shp')
# bridges.to_file(r'C:\Stefan\OSM\bridges.shp')
# tunnels.to_file(r'C:\Stefan\OSM\tunnels.shp')


