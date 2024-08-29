import geopandas

shpfile = geopandas.read_file('~/Downloads/ne_50m_admin_1_states_provinces/ne_50m_admin_1_states_provinces.shp')
shpfile.to_file('states_boundaries.geojson', driver='GeoJSON')