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
        # Assuming cta_sodapy3_api_key is defined in a previous cell
        # Unauthenticated client.
        client = Socrata("data.cityofchicago.org", cta_sodapy3_api_key)
        results = client.get("xbyr-jnvx", limit=2000)
        print("Data fetched successfully.")
    except NameError:
        print("Error: cta_sodapy3_api_key is not defined. Please ensure the cell defining cta_sodapy3_api_key is run.")
        results = None # Set results to None if cta_sodapy3_api_key is not defined
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
    return trains_list

def getStations():
    # --- Data Fetching ---
    try:
        # Assuming cta_sodapy3_api_key is defined in a previous cell
        # Unauthenticated client.
        client = Socrata("data.cityofchicago.org", cta_sodapy3_api_key)
        station_results = client.get("8pix-ypme", limit=2000)
        print("CTA train station data fetched successfully.")
    except NameError:
        print("Error: cta_sodapy3_api_key is not defined. Please ensure the cell defining cta_sodapy3_api_key is run.")
        station_results = None # Set results to None if cta_sodapy3_api_key is not defined
    except Exception as e:
        print(f"Error fetching data: {e}")
        station_results = None

    # Check if station_results is not None or empty
    if not station_results:
        print("Station results is empty or None, cannot proceed.")
    else:
        print("Station data headers:", list(station_results[0].keys()))

    

    return station_results

def plotRoutesAndStations(m):

    print("Plotting route geometries on the map...")

    results = getRoutes()
    new_station_results = getStations()

    brown_line_geometries = []
    orange_line_geometries = []
    green_line_geometries = []
    pink_line_geometries = []
    purple_line_geometries = []
    blue_line_geometries = []
    red_line_geometries = []
    yellow_line_geometries = []

    red_line_color = '#' + line_colors.get('Red Line', 'c60c30')
    blue_line_color = '#' + line_colors.get('Blue Line', '00a1de')
    yellow_line_color = '#' + line_colors.get('Yellow Line', 'f9e300')
    purple_line_color = '#' + line_colors.get('Purple Line', '522398')
    brown_line_color = '#' + line_colors.get('Brown Line', '62361b')
    green_line_color = '#' + line_colors.get('Green Line', '009b3a')
    orange_line_color = '#' + line_colors.get('Orange Line', 'f9461c')
    pink_line_color = '#' + line_colors.get('Pink Line', 'e27ea6')

    red_offset_lon = 0.0001
    red_offset_lat = 0.0001
    blue_offset_lon = 0.0000
    blue_offset_lat = 0.0000
    yellow_offset_lon = -0.0001
    yellow_offset_lat = 0.0000
    purple_offset_lon = 0.0000
    purple_offset_lat = -0.0000
    brown_offset_lon = -0.0001
    brown_offset_lat = -0.0001
    green_offset_lon = 0.0002
    green_offset_lat = 0.0002
    orange_offset_lon = -0.0002
    orange_offset_lat = -0.0002
    pink_offset_lon = 0.0001
    pink_offset_lat = 0.0001

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
 
    # Plot Red Line with offset
    if red_line_geometries:        
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
        print("Red Line geometries added to the map.")

    # Plot Blue Line with offset
    if blue_line_geometries:
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
        print("Blue Line geometries added to the map.")

    # Plot Yellow Line with offset
    if yellow_line_geometries:
        for geometry in yellow_line_geometries:
            if geometry.get('type') == 'MultiLineString':
                offset_multilinestring = []
                for linestring_coords in geometry.get('coordinates', []):
                    offset_multilinestring.append(offset_coordinates(linestring_coords, yellow_offset_lon, yellow_offset_lat))
                offset_geometry = {'type': 'MultiLineString', 'coordinates': offset_multilinestring}
                folium.features.GeoJson(
                    offset_geometry,
                    style_function=lambda x: {'color': yellow_line_color, 'weight': 3}
                ).add_to(m)
            elif geometry.get('type') == 'LineString':
                offset_linestring = offset_coordinates(geometry.get('coordinates', []), yellow_offset_lon, yellow_offset_lat)
                offset_geometry = {'type': 'LineString', 'coordinates': offset_linestring}
                folium.features.GeoJson(
                    offset_geometry,
                    style_function=lambda x: {'color': yellow_line_color, 'weight': 3}
                ).add_to(m)
        print("Yellow Line geometries added to the map.")

    # Plot Purple Line with offset and dashed style  
    if purple_line_geometries:
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
        print("Purple Line geometries added to the map as dashed lines.")

    # Plot Brown Line with offset   
    if brown_line_geometries:
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
        print("Brown Line geometries added to the map.")

    # Plot Green Line with offset
    if green_line_geometries:
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
        print("Green Line geometries added to the map.")

    # Plot Orange Line with offset
    if orange_line_geometries:        
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
        print("Orange Line geometries added to the map.")

    # Plot Pink Line with offset
    if pink_line_geometries:
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
        print("Pink Line geometries added to the map.")

    # Set to keep track of plotted stations by map_id
    plotted_stations = set()
    # Plot Yellow Line stations
    if new_station_results:
        # print("Plotting Yellow Line stations...")
        for station in new_station_results:
            print("Processing station:", station.get('station_name'))
            map_id = station.get('map_id')
            # Check if the station is on the Yellow Line and hasn't been plotted yet
            if (station.get('y') == True or station.get('y') == 'true') and map_id not in plotted_stations:
                try:
                    latitude = float(station.get('location', {}).get('latitude'))
                    longitude = float(station.get('location', {}).get('longitude'))
                    # Apply the same offset as the Yellow Line geometries
                    offset_latitude = latitude + yellow_offset_lat
                    offset_longitude = longitude + yellow_offset_lon
                    folium.CircleMarker(
                        location=[offset_latitude, offset_longitude],
                        radius=5,
                        color=yellow_line_color,
                        fill=True,
                        fill_color='white',
                        fill_opacity=1.0,
                        tooltip=station.get('station_name')
                    ).add_to(m)
                    plotted_stations.add(map_id) # Add map_id to the set of plotted stations
                    print(f"Plotted Yellow Line station: {station.get('station_name')}")
                except (ValueError, TypeError):
                    print(f"Skipping Yellow Line station due to invalid location data: {station.get('station_name')}")
    print("Yellow Line stations added to the map.")

    # Set to keep track of plotted stations by map_id
    plotted_stations = set()
    # Plot Red Line stations
    if new_station_results:
        for station in new_station_results:
            map_id = station.get('map_id')
            # Check if the station is on the Red Line and hasn't been plotted yet
            if (station.get('red') == True or station.get('red') == 'true') and map_id not in plotted_stations:
                try:
                    latitude = float(station.get('location', {}).get('latitude'))
                    longitude = float(station.get('location', {}).get('longitude'))
                    # Apply the same offset as the Brown Line geometries
                    offset_latitude = latitude + red_offset_lat
                    offset_longitude = longitude + red_offset_lon
                    folium.CircleMarker(
                        location=[offset_latitude, offset_longitude],
                        radius=5,
                        color=red_line_color,
                        fill=True,
                        fill_color='white',
                        fill_opacity=1.0,
                        tooltip=station.get('station_name')
                    ).add_to(m)
                    plotted_stations.add(map_id) # Add map_id to the set of plotted stations
                except (ValueError, TypeError):
                    print(f"Skipping Red Line station due to invalid location data: {station.get('station_name')}")
    print("Red Line stations added to the map.")

    # Set to keep track of plotted stations by map_id
    plotted_stations = set()
    # Plot Purple Line stations
    if new_station_results:
        for station in new_station_results:
            map_id = station.get('map_id')
            # Check if the station is on the Purple Line and hasn't been plotted yet
            if (station.get('p') == True or station.get('p') == 'true' or station.get('pexp') == True or station.get('pexp') == 'true') and map_id not in plotted_stations:
                try:
                    latitude = float(station.get('location', {}).get('latitude'))
                    longitude = float(station.get('location', {}).get('longitude'))
                    # Apply the same offset as the Purple Line geometries
                    offset_latitude = latitude + purple_offset_lat
                    offset_longitude = longitude + purple_offset_lon
                    folium.CircleMarker(
                        location=[offset_latitude, offset_longitude],
                        radius=5,
                        color=purple_line_color,
                        fill=True,
                        fill_color='white',
                        fill_opacity=1.0,
                        tooltip=station.get('station_name')
                    ).add_to(m)
                    plotted_stations.add(map_id) # Add map_id to the set of plotted stations
                except (ValueError, TypeError):
                    print(f"Skipping Purple Line station due to invalid location data: {station.get('station_name')}")
    print("Purple Line stations added to the map.")

    # Set to keep track of plotted stations by map_id
    plotted_stations = set()
    # Plot Brown Line stations
    if new_station_results:
        for station in new_station_results:
            map_id = station.get('map_id')
            # Check if the station is on the Brown Line and hasn't been plotted yet
            if (station.get('brn') == True or station.get('brn') == 'true') and map_id not in plotted_stations:
                try:
                    latitude = float(station.get('location', {}).get('latitude'))
                    longitude = float(station.get('location', {}).get('longitude'))
                    # Apply the same offset as the Brown Line geometries
                    offset_latitude = latitude + brown_offset_lat
                    offset_longitude = longitude + brown_offset_lon
                    folium.CircleMarker(
                        location=[offset_latitude, offset_longitude],
                        radius=5,
                        color=brown_line_color,
                        fill=True,
                        fill_color='white',
                        fill_opacity=1.0,
                        tooltip=station.get('station_name')
                    ).add_to(m)
                    plotted_stations.add(map_id) # Add map_id to the set of plotted stations
                except (ValueError, TypeError):
                    print(f"Skipping Brown Line station due to invalid location data: {station.get('station_name')}")
    print("Brown Line stations added to the map.")

    # Set to keep track of plotted stations by map_id
    plotted_stations = set()
    # Plot Orange Line stations
    if new_station_results:
        for station in new_station_results:
            map_id = station.get('map_id')
            # Check if the station is on the Orange Line and hasn't been plotted yet
            if (station.get('o') == True or station.get('o') == 'true') and map_id not in plotted_stations:
                try:
                    latitude = float(station.get('location', {}).get('latitude'))
                    longitude = float(station.get('location', {}).get('longitude'))
                    # Apply the same offset as the Orange Line geometries
                    offset_latitude = latitude + orange_offset_lat
                    offset_longitude = longitude + orange_offset_lon
                    folium.CircleMarker(
                        location=[offset_latitude, offset_longitude],
                        radius=5,
                        color=orange_line_color,
                        fill=True,
                        fill_color='white',
                        fill_opacity=1.0,
                        tooltip=station.get('station_name')
                    ).add_to(m)
                    plotted_stations.add(map_id) # Add map_id to the set of plotted stations
                except (ValueError, TypeError):
                    print(f"Skipping Orange Line station due to invalid location data: {station.get('station_name')}")
    print("Orange Line stations added to the map.")

    # Set to keep track of plotted stations by map_id
    plotted_stations = set()
    # Plot Green Line stations
    if new_station_results:
        for station in new_station_results:
            map_id = station.get('map_id')
            # Check if the station is on the Green Line and hasn't been plotted yet
            if (station.get('g') == True or station.get('g') == 'true') and map_id not in plotted_stations:
                try:
                    latitude = float(station.get('location', {}).get('latitude'))
                    longitude = float(station.get('location', {}).get('longitude'))
                    # Apply the same offset as the Green Line geometries
                    offset_latitude = latitude + green_offset_lat
                    offset_longitude = longitude + green_offset_lon
                    folium.CircleMarker(
                        location=[offset_latitude, offset_longitude],
                        radius=5,
                        color=green_line_color,
                        fill=True,
                        fill_color='white',
                        fill_opacity=1.0,
                        tooltip=station.get('station_name')
                    ).add_to(m)
                    plotted_stations.add(map_id) # Add map_id to the set of plotted stations
                except (ValueError, TypeError):
                    print(f"Skipping Green Line station due to invalid location data: {station.get('station_name')}")
    print("Green Line stations added to the map.")

    # Set to keep track of plotted stations by map_id
    plotted_stations = set()
    # Plot Pink Line stations
    if new_station_results:
        for station in new_station_results:
            map_id = station.get('map_id')
            # Check if the station is on the Pink Line and hasn't been plotted yet
            if (station.get('pnk') == True or station.get('pnk') == 'true') and map_id not in plotted_stations:
                try:
                    latitude = float(station.get('location', {}).get('latitude'))
                    longitude = float(station.get('location', {}).get('longitude'))
                    # Apply the same offset as the Pink Line geometries
                    offset_latitude = latitude + pink_offset_lat
                    offset_longitude = longitude + pink_offset_lon
                    folium.CircleMarker(
                        location=[offset_latitude, offset_longitude],
                        radius=5,
                        color=pink_line_color,
                        fill=True,
                        fill_color='white',
                        fill_opacity=1.0,
                        tooltip=station.get('station_name')
                    ).add_to(m)
                    plotted_stations.add(map_id) # Add map_id to the set of plotted stations
                except (ValueError, TypeError):
                    print(f"Skipping Pink Line station due to invalid location data: {station.get('station_name')}")
    print("Pink Line stations added to the map.")

    # Set to keep track of plotted stations by map_id
    plotted_stations = set()
    # Plot Blue Line stations
    if new_station_results:
        for station in new_station_results:
            map_id = station.get('map_id')
            # Check if the station is on the Blue Line and hasn't been plotted yet
            if (station.get('blue') == True or station.get('blue') == 'true') and map_id not in plotted_stations:
                try:
                    latitude = float(station.get('location', {}).get('latitude'))
                    longitude = float(station.get('location', {}).get('longitude'))
                    # Apply the same offset as the Blue Line geometries
                    offset_latitude = latitude + blue_offset_lat
                    offset_longitude = longitude + blue_offset_lon
                    folium.CircleMarker(
                        location=[offset_latitude, offset_longitude],
                        radius=5,
                        color=blue_line_color,
                        fill=True,
                        fill_color='white',
                        fill_opacity=1.0,
                        tooltip=station.get('station_name')
                    ).add_to(m)
                    plotted_stations.add(map_id) # Add map_id to the set of plotted stations
                except (ValueError, TypeError):
                    print(f"Skipping Blue Line station due to invalid location data: {station.get('station_name')}")
    print("Blue Line stations added to the map.")


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

def newMap():

    m = folium.Map(location=[41.8781, -87.6298], zoom_start=11, tiles='USGS.USImagery') # OpenStreetMap provides some aerial views, or consider 'Stamen Terrain' or 'Stamen Toner'
    return m

def createCity():

    m = newMap()
    # m = plotRuns(m, "RED")
    m = plotRoutesAndStations(m)
    
    return m

def main():
    
    map_file = "map.html"
    
    m = createCity()
    # m = plotRuns(m, "RED")

    m.save(map_file)
    
    # Get absolute path and create a file URL
    abs_path = os.path.abspath(map_file)
    
    webview.create_window('CTA Tracker', f'file://{abs_path}')
    webview.start()
    
    if os.path.exists(map_file):
        os.remove(map_file)

if __name__ == "__main__":
    main()

