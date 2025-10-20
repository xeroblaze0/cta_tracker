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
from folium.features import FeatureGroup
from folium import LayerControl

from sodapy import Socrata # Ensure Socrata is imported if fetching data here

cta_api_key = 'edf3d5c3786946c490b5afceeedaf8da'
cta_sodapy3_api_key = 'yOfRulGKwCUS1OriSdIyNl0Q6'

follow_url = 'https://lapi.transitchicago.com/api/1.0/ttfollow.aspx'
arrivals_url = 'http://lapi.transitchicago.com/api/1.0/ttarrivals.aspx'
positions_url = 'http://lapi.transitchicago.com/api/1.0/ttpositions.aspx'
cta_soda3_api_endpoint_url='https://data.cityofchicago.org/api/v3/views/xbyr-jnvx/query.geojson'

line_colors = {
    'Red Line': {
        'legend': 'Red Line',
        'color_id': '#c60c30',
        'lines': ['Red Line', 'Red'],
        'l_stop_boolean': ['red'],
        'geometries': [],
        'stations': [],
        'feature_group': FeatureGroup(name='Red Line'),
        'line_color': '#c60c30',
        'offset_lon': 0.0001,
        'offset_lat': 0.0001
    },
    'Blue Line': {
        'legend': 'Blue Line',
        'color_id': '#00a1de',
        'lines': ['Blue Line', 'Blue Line (O\'Hare)', 'Blue Line (Forest Park)', 'Blue'],
        'l_stop_boolean': ['blue'],
        'geometries': [],
        'feature_group': FeatureGroup(name='Blue Line'),
        'line_color': '#00a1de',
        'offset_lon': 0.0,
        'offset_lat': 0.0
    },
    'Brown Line': {
        'legend': 'Brown Line',
        'color_id': '#62361b',
        'lines': ['Brown Line', 'Brown'],
        'l_stop_boolean': ['brn'],
        'geometries': [],
        'feature_group': FeatureGroup(name='Brown Line'),
        'line_color': '#62361b',
        'offset_lon': -0.0001,
        'offset_lat': -0.0001
    },
    'Green Line': {
        'legend': 'Green Line',
        'color_id': '#009b3a',
        'lines': ['Green Line', 'Green'],
        'l_stop_boolean': ['g'],
        'geometries': [],
        'feature_group': FeatureGroup(name='Green Line'),
        'line_color': '#009b3a',
        'offset_lon': 0.0002,
        'offset_lat': 0.0002
    },
    'Orange Line': {
        'legend': 'Orange Line',
        'color_id': '#f9461c',
        'lines': ['Orange Line', 'Orange'],
        'l_stop_boolean': ['o'],
        'geometries': [],
        'feature_group': FeatureGroup(name='Orange Line'),
        'line_color': '#f9461c',
        'offset_lon': -0.0002,
        'offset_lat': -0.0002
    },
    'Purple Line': {
        'legend': 'Purple Line',
        'color_id': '#522398',
        'lines': ['Purple Line', 'Purple', 'Purple (Express)', 'Purple (Exp)'],
        'l_stop_boolean': ['p', 'pexp'],
        'geometries': [],
        'feature_group': FeatureGroup(name='Purple Line'),
        'line_color': '#522398',
        'offset_lon': 0.0,
        'offset_lat': 0.0
    },
    'Pink Line': {
        'legend': 'Pink Line',
        'color_id': '#e27ea6',
        'lines': ['Pink Line', 'Pink'],
        'l_stop_boolean': ['pnk'],
        'geometries': [],
        'feature_group': FeatureGroup(name='Pink Line'),
        'line_color': '#e27ea6',
        'offset_lon': 0.0001,
        'offset_lat': 0.0001
    },
    'Yellow Line': {
        'legend': 'Yellow Line',
        'color_id': '#f9e300',
        'lines': ['Yellow Line', 'Yellow'],
        'l_stop_boolean': ['y'],
        'geometries': [],
        'feature_group': FeatureGroup(name='Yellow Line'),
        'line_color': '#f9e300',
        'offset_lon': -0.0001,
        'offset_lat': 0.0
    }
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

    print("Fetching and processing all route geometries from CTA...")

    # --- Data Fetching ---
    try:
        client = Socrata("data.cityofchicago.org", cta_sodapy3_api_key)
        results = client.get("xbyr-jnvx", limit=2000)
        # print("Data fetched successfully.")
    except NameError:
        print("Error: cta_sodapy3_api_key is not defined.")
        return
    except Exception as e:
        print(f"Error fetching data: {e}")
        return

    if not results:
        print("No route data returned from API.")
        return

    # Clear existing geometries before populating
    for line in line_colors:
        if isinstance(line_colors[line], dict):
            line_colors[line]['geometries'] = []

    # Iterate through results and assign geometries to the correct line
    for item in results:
        if isinstance(item, dict) and 'the_geom' in item and isinstance(item['the_geom'], dict):
            for line_name, line_details in line_colors.items():
                if isinstance(line_details, dict):
                    # if 'legend' in item and item.get('legend') == line_details['legend']:
                    if 'lines' in item and any(line_id in item.get('lines', '') for line_id in line_details['lines']):
                        line_details['geometries'].append(item['the_geom'])

    # for line_name, line_details in line_colors.items():
    #     if isinstance(line_details, dict):
    #         print(f"Found {len(line_details['geometries'])} geometries for the {line_details['legend']}.")

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
    return trains_list

def getStations():

    print("Fetching and processing all station" \
    " geometries from CTA...")
    # --- Data Fetching ---
    try:
        # Unauthenticated client.
        # https://data.cityofchicago.org/Transportation/CTA-System-Information-List-of-L-Stops/8pix-ypme/about_data
        client = Socrata("data.cityofchicago.org", cta_sodapy3_api_key)
        station_results = client.get("8pix-ypme", limit=2000)
        # print("CTA train station data fetched successfully.")
    except NameError:
        print("Error: cta_sodapy3_api_key is not defined. Please ensure the cell defining cta_sodapy3_api_key is run.")
        return
    except Exception as e:
        print(f"Error fetching data: {e}")
        return

    # Clear existing stations before populating
    for line in line_colors:
        if isinstance(line_colors[line], dict):
            line_colors[line]['stations'] = []

    if station_results:
        for station in station_results:
            for line_name, line_details in line_colors.items():
                if isinstance(line_details, dict):
                    if any(str(station.get(l_stop, '')).lower() in ['true', '1'] for l_stop in line_details['l_stop_boolean']):
                        line_details['stations'].append(station)
    
    # for line_name, line_details in line_colors.items():
    #     if isinstance(line_details, dict):
    #         print(f"Found {len(line_details['stations'])} stations for the {line_details['legend']}.")

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

def plotTrainLine(m, line_details):

    # print(f"Plotting {line_details['legend']} geometries on the map...")

    line_geometries = line_details['geometries']
    station_results = line_details['stations']

    line_group = line_details['feature_group']
    line_color = line_details['line_color']
    offset_lon = line_details['offset_lon']
    offset_lat = line_details['offset_lat']

    if line_geometries:
        for geometry in line_geometries:
            if geometry.get('type') == 'MultiLineString':
                offset_multilinestring = []
                for linestring_coords in geometry.get('coordinates', []):
                    offset_multilinestring.append(offset_coordinates(linestring_coords, offset_lon, offset_lat))
                offset_geometry = {'type': 'MultiLineString', 'coordinates': offset_multilinestring}
                folium.features.GeoJson(
                    offset_geometry,
                    style_function=lambda x, color=line_color: {'color': color, 'weight': 3}
                ).add_to(line_group) # Add to FeatureGroup
            elif geometry.get('type') == 'LineString':
                offset_linestring = offset_coordinates(geometry.get('coordinates', []), offset_lon, offset_lat)
                offset_geometry = {'type': 'LineString', 'coordinates': offset_linestring}
                folium.features.GeoJson(
                    offset_geometry,
                    style_function=lambda x, color=line_color: {'color': color, 'weight': 3}
                ).add_to(line_group) # Add to FeatureGroup
        # print(f"{line_details['legend']} geometries added to the {line_details['legend']} FeatureGroup with offset.")

    # Set to keep track of plotted stations by map_id
    plotted_stations = set()
    # Plot stations
    if station_results:
        for station in station_results:
            map_id = station.get('map_id')
            # Check if the station hasn't been plotted yet
            if map_id not in plotted_stations:
                try:
                    latitude = float(station.get('location', {}).get('latitude'))
                    longitude = float(station.get('location', {}).get('longitude'))
                    # Apply the same offset as the line geometries
                    offset_latitude = latitude + offset_lat
                    offset_longitude = longitude + offset_lon
                    folium.CircleMarker(
                        location=[offset_latitude, offset_longitude],
                        radius=5,
                        color=line_color,
                        fill=True,
                        fill_color='white',
                        fill_opacity=1.0,
                        tooltip=station.get('station_name')
                    ).add_to(line_group)
                    plotted_stations.add(map_id) # Add map_id to the set of plotted stations
                except (ValueError, TypeError):
                    print(f"Skipping {line_details['legend']} station due to invalid location data: {station.get('station_name')}")
    # print(f"{line_details['legend']} stations added to the map.")

    # Add FeatureGroup to map
    line_group.add_to(m)

    return m

def newMap():

    m = folium.Map(location=[41.8781, -87.6298], zoom_start=11, tiles='USGS.USImagery') # OpenStreetMap provides some aerial views, or consider 'Stamen Terrain' or 'Stamen Toner'
    return m

def createCity():

    m = newMap()

    getRoutes() # Fetch and process all routes once
    getStations() # Fetch and process all stations once
    
    for line_details in line_colors.values():
        m = plotTrainLine(m, line_details)
    
    return m

def main():
    
    map_file = "map.html"
    
    m = createCity()
    # m = plotRuns(m, "RED")

    LayerControl().add_to(m)
    m.save(map_file)
    
    # Get absolute path and create a file URL
    abs_path = os.path.abspath(map_file)
    
    webview.create_window('CTA Tracker', f'file://{abs_path}')
    webview.start()
    
    if os.path.exists(map_file):
        os.remove(map_file)

if __name__ == "__main__":
    main()

