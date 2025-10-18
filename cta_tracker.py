import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
import math
import requests
import webview
import os

from datetime import datetime as dt

from IPython.display import Image
from IPython.display import HTML

import folium
import folium.plugins as plugins

from sodapy import Socrata # Ensure Socrata is imported if fetching data here

# from sklearn.preprocessing import MinMaxScaler

# from arcgis.gis import GIS
# from arcgis.geometry import Point, Polyline, Polygon
# from arcgis.raster import Raster
# from arcgis.map.symbols import SimpleMarkerSymbolEsriSMS, SimpleLineSymbolEsriSLS, SimpleFillSymbolEsriSFS, SimpleFillSymbolStyle, SimpleMarkerSymbolStyle, SimpleLineSymbolStyle
# from arcgis.map.popups import PopupInfo

# from s2cloudless import S2PixelCloudDetector

cta_api_key = 'edf3d5c3786946c490b5afceeedaf8da'
cta_sodapy3_api_key = 'yOfRulGKwCUS1OriSdIyNl0Q6'

follow_url = 'https://lapi.transitchicago.com/api/1.0/ttfollow.aspx'
arrivals_url = 'http://lapi.transitchicago.com/api/1.0/ttarrivals.aspx'
positions_url = 'http://lapi.transitchicago.com/api/1.0/ttpositions.aspx'
cta_soda3_api_endpoint_url='https://data.cityofchicago.org/api/v3/views/xbyr-jnvx/query.geojson'

# Define line_colors dictionary within this cell
line_colors = {
    'Red Line': 'c60c30',
    'Red': 'c60c30',
    'Blue Line': '00a1de',
    'Blue Line (O\'Hare)': '00a1de',
    'Blue Line (Forest Park)': '00a1de',
    'Blue': '00a1de',
    'Brown Line': '62361b',
    'Brown': '62361b',
    'Green Line': '009b3a',
    'Green': '009b3a',
    'Orange Line': 'f9461c',
    'Orange': 'f9461c',
    'Purple Line': '522398',
    'Purple': '522398',
    'Purple Line (Express)': '522398',
    'Purple (Express)': '522398',
    'Purple Line (Exp)': '522398',
    'Purple (Exp)': '522398',
    'Purple': '522398',
    'Pink Line': 'e27ea6',
    'Pink': 'e27ea6',
    'Yellow Line': 'f9e300',
    'Yellow': 'f9e300'
}

def offset_coordinates(coords, offset_amount_degrees_lon=0.0, offset_amount_degrees_lat=0.0):
    """
    Applies a small offset to coordinates to separate overlapping lines.
    Applies a constant shift to longitude and latitude.
    """
    offset_coords = []
    for coord_pair in coords:
        # Assuming coord_pair is [longitude, latitude]
        offset_coords.append([coord_pair[0] + offset_amount_degrees_lon, coord_pair[1] + offset_amount_degrees_lat])
    return offset_coords

def getRoutes():

    print("Fetching route geometries from Socrata...")

    # --- Data Fetching ---
    try:
        # Assuming app_token is defined in a previous cell
        # Unauthenticated client.
        client = Socrata("data.cityofchicago.org", cta_sodapy3_api_key)
        results = client.get("xbyr-jnvx", limit=2000)
        print("Data fetched successfully.")
    except NameError:
        print("Error: app_token is not defined. Please ensure the cell defining app_token is run.")
        results = None # Set results to None if app_token is not defined
    except Exception as e:
        print(f"Error fetching data: {e}")
        results = None

    return results

def getRuns(rt):
    # rt is route color, e.g. "RED", "BLUE", "G", "P", "Y", "BR", "P"
    # returuns list of run numbers for that line

    params = {
        "key": cta_api_key,
        "rt": rt,
        "outputType": "JSON"
    }
    
    try:
        response = requests.get(positions_url, params=params)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()  # Or response.text for non-JSON responses

        # Process the data
        # print(data)

    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")

    trains_list = data['ctatt']['route'][0]['train']

    # print(runs)
    return(trains_list)

def plotRoutes(m):

    print("Plotting route geometries on the map...")
    results = getRoutes()

    brown_line_geometries = []
    orange_line_geometries = []
    green_line_geometries = []
    pink_line_geometries = []
    purple_line_geometries = []
    blue_line_geometries = []
    red_line_geometries = []
    yellow_line_geometries = []

    if results:
        for item in results:
            if isinstance(item, dict) and 'the_geom' in item and isinstance(item['the_geom'], dict):
                # Check for Brown Line
                if ('legend' in item and item.get('legend') == 'BR') or \
                ('lines' in item and 'brown' in item.get('lines', '').lower()):
                    brown_line_geometries.append(item['the_geom'])

                # Check for Orange Line
                if ('legend' in item and item.get('legend') == 'OR') or \
                ('lines' in item and 'orange' in item.get('lines', '').lower()):
                    orange_line_geometries.append(item['the_geom'])

                # Check for Green Line
                if ('legend' in item and item.get('legend') == 'GR') or \
                ('lines' in item and 'green' in item.get('lines', '').lower()):
                    green_line_geometries.append(item['the_geom'])

                # Check for Pink Line
                if ('legend' in item and item.get('legend') == 'PK') or \
                ('lines' in item and 'pink' in item.get('lines', '').lower()):
                    pink_line_geometries.append(item['the_geom'])

                # Check for Purple Line
                if ('legend' in item and item.get('legend') == 'PR') or \
                ('lines' in item and 'purple' in item.get('lines', '').lower()):
                    purple_line_geometries.append(item['the_geom'])

                # Check for Blue Line
                if ('legend' in item and item.get('legend') == 'BL') or \
                ('lines' in item and 'blue' in item.get('lines', '').lower()):
                    blue_line_geometries.append(item['the_geom'])

                # Check for Red Line
                if ('legend' in item and item.get('legend') == 'RD') or \
                ('lines' in item and 'red' in item.get('lines', '').lower()):
                    red_line_geometries.append(item['the_geom'])

                # Check for Yellow Line
                if ('legend' in item and item.get('legend') == 'YL') or \
                ('lines' in item and 'yellow' in item.get('lines', '').lower()):
                    yellow_line_geometries.append(item['the_geom'])


        print(f"Found {len(brown_line_geometries)} geometries for the Brown Line.")
        print(f"Found {len(orange_line_geometries)} geometries for the Orange Line.")
        print(f"Found {len(green_line_geometries)} geometries for the Green Line.")
        print(f"Found {len(pink_line_geometries)} geometries for the Pink Line.")
        print(f"Found {len(purple_line_geometries)} geometries for the Purple Line.")
        print(f"Found {len(blue_line_geometries)} geometries for the Blue Line.")
        print(f"Found {len(red_line_geometries)} geometries for the Red Line.")
        print(f"Found {len(yellow_line_geometries)} geometries for the Yellow Line.")


    else:
        print("Results is empty or None, cannot filter geometries.")

    # Plot Brown Line with offset
    if brown_line_geometries:
        brown_line_color = '#' + line_colors.get('Brown Line', '62361b')
        brown_offset_lon = -0.0002 # Example offset for Brown Line
        brown_offset_lat = -0.0002 # Example offset for Brown Line
        for geometry in brown_line_geometries:
            if geometry.get('type') == 'MultiLineString':
                offset_multilinestring = []
                for linestring_coords in geometry.get('coordinates', []):
                    offset_multilinestring.append(offset_coordinates(linestring_coords, brown_offset_lon, brown_offset_lat))
                offset_geometry = {'type': 'MultiLineString', 'coordinates': offset_multilinestring}
                folium.features.GeoJson(
                    offset_geometry,
                    style_function=lambda x: {'color': brown_line_color, 'weight': 3}
                ).add_to(m)
            elif geometry.get('type') == 'LineString':
                offset_linestring = offset_coordinates(geometry.get('coordinates', []), brown_offset_lon, brown_offset_lat)
                offset_geometry = {'type': 'LineString', 'coordinates': offset_linestring}
                folium.features.GeoJson(
                    offset_geometry,
                    style_function=lambda x: {'color': brown_line_color, 'weight': 3}
                ).add_to(m)
        print("Brown Line geometries added to the map with offset.")


    # Plot Orange Line with offset
    if orange_line_geometries:
        orange_line_color = '#' + line_colors.get('Orange Line', 'f9461c')
        orange_offset_lon = 0.0001
        orange_offset_lat = 0.0001
        for geometry in orange_line_geometries:
            if geometry.get('type') == 'MultiLineString':
                offset_multilinestring = []
                for linestring_coords in geometry.get('coordinates', []):
                    offset_multilinestring.append(offset_coordinates(linestring_coords, orange_offset_lon, orange_offset_lat))
                offset_geometry = {'type': 'MultiLineString', 'coordinates': offset_multilinestring}
                folium.features.GeoJson(
                    offset_geometry,
                    style_function=lambda x: {'color': orange_line_color, 'weight': 3}
                ).add_to(m)
            elif geometry.get('type') == 'LineString':
                offset_linestring = offset_coordinates(geometry.get('coordinates', []), orange_offset_lon, orange_offset_lat)
                offset_geometry = {'type': 'LineString', 'coordinates': offset_linestring}
                folium.features.GeoJson(
                    offset_geometry,
                    style_function=lambda x: {'color': orange_line_color, 'weight': 3}
                ).add_to(m)
        print("Orange Line geometries added to the map with offset.")


    # Plot Green Line with offset
    if green_line_geometries:
        green_line_color = '#' + line_colors.get('Green Line', '009b3a')
        green_offset_lon = -0.0001
        green_offset_lat = -0.0001
        for geometry in green_line_geometries:
            if geometry.get('type') == 'MultiLineString':
                offset_multilinestring = []
                for linestring_coords in geometry.get('coordinates', []):
                    offset_multilinestring.append(offset_coordinates(linestring_coords, green_offset_lon, green_offset_lat))
                offset_geometry = {'type': 'MultiLineString', 'coordinates': offset_multilinestring}
                folium.features.GeoJson(
                    offset_geometry,
                    style_function=lambda x: {'color': green_line_color, 'weight': 3}
                ).add_to(m)
            elif geometry.get('type') == 'LineString':
                offset_linestring = offset_coordinates(geometry.get('coordinates', []), green_offset_lon, green_offset_lat)
                offset_geometry = {'type': 'LineString', 'coordinates': offset_linestring}
                folium.features.GeoJson(
                    offset_geometry,
                    style_function=lambda x: {'color': green_line_color, 'weight': 3}
                ).add_to(m)
        print("Green Line geometries added to the map with offset.")

    # Plot Pink Line with offset
    if pink_line_geometries:
        pink_line_color = '#' + line_colors.get('Pink Line', 'e27ea6')
        pink_offset_lon = 0.0002
        pink_offset_lat = 0.0002
        for geometry in pink_line_geometries:
            if geometry.get('type') == 'MultiLineString':
                offset_multilinestring = []
                for linestring_coords in geometry.get('coordinates', []):
                    offset_multilinestring.append(offset_coordinates(linestring_coords, pink_offset_lon, pink_offset_lat))
                offset_geometry = {'type': 'MultiLineString', 'coordinates': offset_multilinestring}
                folium.features.GeoJson(
                    offset_geometry,
                    style_function=lambda x: {'color': pink_line_color, 'weight': 3}
                ).add_to(m)
            elif geometry.get('type') == 'LineString':
                offset_linestring = offset_coordinates(geometry.get('coordinates', []), pink_offset_lon, pink_offset_lat)
                offset_geometry = {'type': 'LineString', 'coordinates': offset_linestring}
                folium.features.GeoJson(
                    offset_geometry,
                    style_function=lambda x: {'color': pink_line_color, 'weight': 3}
                ).add_to(m)
        print("Pink Line geometries added to the map with offset.")

    # Plot Purple Line with horizontal offset and dashed style
    if purple_line_geometries:
        purple_line_color = '#' + line_colors.get('Purple Line', '522398')
        purple_offset_lon = 0.0002
        purple_offset_lat = 0.0
        for geometry in purple_line_geometries:
            if geometry.get('type') == 'MultiLineString':
                offset_multilinestring = []
                for linestring_coords in geometry.get('coordinates', []):
                    offset_multilinestring.append(offset_coordinates(linestring_coords, purple_offset_lon, purple_offset_lat))
                offset_geometry = {'type': 'MultiLineString', 'coordinates': offset_multilinestring}
                folium.features.GeoJson(
                    offset_geometry,
                    style_function=lambda x: {'color': purple_line_color, 'weight': 3, 'dashArray': '5, 5'}
                ).add_to(m)
            elif geometry.get('type') == 'LineString':
                offset_linestring = offset_coordinates(geometry.get('coordinates', []), purple_offset_lon, purple_offset_lat)
                offset_geometry = {'type': 'LineString', 'coordinates': offset_linestring}
                folium.features.GeoJson(
                    offset_geometry,
                    style_function=lambda x: {'color': purple_line_color, 'weight': 3, 'dashArray': '5, 5'}
                ).add_to(m)
        print("Purple Line geometries added to the map as dashed lines with horizontal offset.")

    # Plot Blue Line with offset
    if blue_line_geometries:
        blue_line_color = '#' + line_colors.get('Blue Line', '00a1de')
        blue_offset_lon = 0.000
        blue_offset_lat = 0.000
        for geometry in blue_line_geometries:
            if geometry.get('type') == 'MultiLineString':
                offset_multilinestring = []
                for linestring_coords in geometry.get('coordinates', []):
                    offset_multilinestring.append(offset_coordinates(linestring_coords, blue_offset_lon, blue_offset_lat))
                offset_geometry = {'type': 'MultiLineString', 'coordinates': offset_multilinestring}
                folium.features.GeoJson(
                    offset_geometry,
                    style_function=lambda x: {'color': blue_line_color, 'weight': 3}
                ).add_to(m)
            elif geometry.get('type') == 'LineString':
                offset_linestring = offset_coordinates(geometry.get('coordinates', []), blue_offset_lon, blue_offset_lat)
                offset_geometry = {'type': 'LineString', 'coordinates': offset_linestring}
                folium.features.GeoJson(
                    offset_geometry,
                    style_function=lambda x: {'color': blue_line_color, 'weight': 3}
                ).add_to(m)
        print("All Blue Line geometries added to the map with offset.")

    # Plot Red Line with offset
    if red_line_geometries:
        red_line_color = '#' + line_colors.get('Red Line', 'c60c30')
        red_offset_lon = 0.000
        red_offset_lat = 0.000
        for geometry in red_line_geometries:
            if geometry.get('type') == 'MultiLineString':
                offset_multilinestring = []
                for linestring_coords in geometry.get('coordinates', []):
                    offset_multilinestring.append(offset_coordinates(linestring_coords, red_offset_lon, red_offset_lat))
                offset_geometry = {'type': 'MultiLineString', 'coordinates': offset_multilinestring}
                folium.features.GeoJson(
                    offset_geometry,
                    style_function=lambda x: {'color': red_line_color, 'weight': 3}
                ).add_to(m)
            elif geometry.get('type') == 'LineString':
                offset_linestring = offset_coordinates(geometry.get('coordinates', []), red_offset_lon, red_offset_lat)
                offset_geometry = {'type': 'LineString', 'coordinates': offset_linestring}
                folium.features.GeoJson(
                    offset_geometry,
                    style_function=lambda x: {'color': red_line_color, 'weight': 3}
                ).add_to(m)
        print("All Red Line geometries added to the map with offset.")

    # Plot Yellow Line (no offset)
    if yellow_line_geometries:
        yellow_line_color = '#' + line_colors.get('Yellow Line', 'f9e300')
        for geometry in yellow_line_geometries:
            if geometry.get('type') in ['MultiLineString', 'LineString']:
                folium.features.GeoJson(
                    geometry,
                    style_function=lambda x: {'color': yellow_line_color, 'weight': 3}
                ).add_to(m)
        print("Yellow Line geometries added to the map.")

    return m

def plotRuns(map, line):

    runs = []
    lats = []
    longs = []
    headings = []

    trains_list=getRuns(line)

    for train in trains_list:

        runs.append(train.get('rn'))
        lats.append(train.get('lat'))
        longs.append(train.get('lon'))
        headings.append(train.get('heading'))

    for i in range(len(runs)):

        html = f'''
        <span class="fa-stack" style="background-color: transparent; border: none;">
            <i class="fa-solid fa-location-pin fa-2x fa-stack-1x" style="color:Tomato; transform: rotate({headings[i]}deg);"></i>
            <i class="fa-solid fa-train-subway fa-stack-1x" style="color:White"></i>
        </span>
        '''

        folium.Marker(
            (lats[i], longs[i]),
            icon=folium.DivIcon(
                icon_anchor=(11,20),
                html=html)
        ).add_to(map)

    return map

def createCity():

    m = folium.Map(location=[41.8781, -87.6298], zoom_start=11, tiles='USGS.USImagery') # OpenStreetMap provides some aerial views, or consider 'Stamen Terrain' or 'Stamen Toner'

    m = plotRoutes(m)
    
    return m

def main():
    
    map_file = "map.html"
    
    m = createCity()
    m = plotRuns(m, "RED")

    m.save(map_file)
    
    # Get absolute path and create a file URL
    abs_path = os.path.abspath(map_file)
    
    webview.create_window('CTA Tracker', f'file://{abs_path}')
    webview.start()
    
    if os.path.exists(map_file):
        os.remove(map_file)

if __name__ == "__main__":
    main()

