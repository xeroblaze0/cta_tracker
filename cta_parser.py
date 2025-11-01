import pandas as pd
import folium
import os

from folium.plugins import TimestampedGeoJson
from folium.features import DivIcon, FeatureGroup, Icon


RT_PARAMS = {"Red", "Blue", "G", "Brn", "P", "Y", "Pink", "Org"}

def load_cta_history_data(limit=None):

    # Stitch data files before loading
    data_dir = '/home/user/Projects/cta_tracker/data'
    output_file = os.path.join(data_dir, 'cta_train_data_full.csv')
    csv_files = [f for f in os.listdir(data_dir) if f.startswith('cta_train_data_') and f.endswith('.csv') and f != 'cta_train_data_full.csv']

    if csv_files:
        print(f"Stitching {len(csv_files)} data files...")
        df_list = [pd.read_csv(os.path.join(data_dir, f)) for f in csv_files]
        full_df = pd.concat(df_list, ignore_index=True)
        full_df.to_csv(output_file, index=False)
        print(f"Successfully stitched files into {output_file}")

    # Load the data from the CSV file
    csv_file_path = '/home/user/Projects/cta_tracker/data/cta_train_data_full.csv'
    
    try:
        trains_df = pd.read_csv(csv_file_path, nrows=limit)
        # print(trains_df.head())
    except FileNotFoundError:
        print(f"Error: The file {csv_file_path} was not found.")
        return None
    except Exception as e:
        print(f"An error occurred while reading the CSV file: {e}")
        return None

    if trains_df.empty:
        print("No data to process.")
        return None

    train_dataframes = {}

    unique_train_numbers = trains_df['rn'].unique()
    unique_train_rts = trains_df['rt'].unique()
    # print(f"Unique train routes in data: {unique_train_rts}")

    for train_number in unique_train_numbers:
        train_dataframes[train_number] = trains_df[trains_df['rn'] == train_number]

    # Concatenate all the DataFrames
    all_train_data = pd.concat(train_dataframes.values(), ignore_index=True)

    # Convert 'tmst' to datetime objects
    all_train_data['tmst'] = pd.to_datetime(all_train_data['tmst'])

    # Sort by 'tmst'
    all_train_data = all_train_data.sort_values(by='tmst')

    # Drop duplicate rows based on 'tmst', 'rn', 'lat', and 'lon'
    all_train_data = all_train_data.drop_duplicates(subset=['tmst', 'rn', 'lat', 'lon'])

    return all_train_data

def draw_map(all_train_data, chicago_map):
    features = []
    for index, row in all_train_data.iterrows():
        feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [row['lon'], row['lat']],
            },
            'properties': {
                'times': [row['tmst'].isoformat()],
                'popup': f"Train: {row['rn']}<br>Time: {row['tmst'].strftime('%Y-%m-%d %H:%M:%S')}<br>Heading: {row['heading']}",
                'icon': 'marker',  # Use 'marker' type for custom icon
                'iconstyle': {
                    'iconUrl': f'https://raw.githubusercontent.com/xeroblaze0/cta_tracker/main/assets/{row["rt"].lower()}_cta.png', # Use the route to select the icon
                    'iconSize': [15, 15], # Size of the icon in pixels (width, height)
                    'iconAnchor': [15, 40], # Anchor point of the icon (x, y) relative to its top-left corner
                    'popupAnchor': [0, -35] # Anchor point for the popup relative to the icon anchor
                }
            }
        }
        # Append the feature to the appropriate FeatureGroup
        # if row['rt'] in route_feature_groups:
        #     route_feature_groups[row['rt']].add_child(folium.Marker(location=[row['lat'], row['lon']], icon=DivIcon(icon_size=(20,20),icon_anchor=(0,0), html=f'<img src="https://raw.githubusercontent.com/xeroblaze0/cta_tracker/main/assets/{row["rt"].lower()}_cta.png" width="20" height="20">')))
        features.append(feature)


    # Add TimestampedGeoJson to the map for all routes
    timestamped_geojson = TimestampedGeoJson({
        'type': 'FeatureCollection',
        'features': features
    },
        period='PT1M',  # Time between points in ISO 8601 duration format (e.g., PT1M for 1 minute)
        add_last_point=True,
        auto_play=False,
        loop=False,
        max_speed=30,
        min_speed=0.1,
        duration='PT1M',
        transition_time=20,
    )

    # Add the TimestampedGeoJson layer to the map
    timestamped_geojson.add_to(chicago_map)

def create_new_map():
    chicago_map = folium.Map(location=[41.8781, -87.6298], zoom_start=12, tiles='Esri World Imagery')
    return chicago_map

def main():
    print("Loading CTA train history data and generating map...")
    # Load the CTA train history data
    cta_history_df = load_cta_history_data(limit=None)

    # Create a new map
    chicago_map = create_new_map()

    # Draw the map with the CTA history data
    draw_map(cta_history_df, chicago_map)

    # Save the map to an HTML file
    chicago_map.save("cta_tracker/cta_train_map.html")
    print("Map has been saved to cta_tracker/cta_train_map.html")

if __name__ == "__main__":
    main()