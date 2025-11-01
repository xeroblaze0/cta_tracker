import requests
import pandas as pd
import time
from datetime import datetime, timedelta

# --- Configuration ---
# Replace with your actual CTA API key
CTA_API_KEY = 'edf3d5c3786946c490b5afceeedaf8da'
BASE_URL = 'http://lapi.transitchicago.com/api/1.0/ttpositions.aspx'
# Fields to extract from the API response: tmst (timestamp), rn (run number), 
# lat (latitude), lon (longitude), and hdg (heading).
RT_PARAMS = {"Red", "Blue", "G", "Brn", "P", "Y", "Pink", "Org"}
DATA_FIELDS = ['rt', 'tmst', 'rn', 'lat', 'lon', 'heading']

# --- Time Configuration ---
# Set the start and end times for data collection in 24-hour format (HH:MM:SS)
COLLECTION_START_TIME = "15:25:00"
COLLECTION_END_TIME = "18:35:00"
SAMPLE_INTERVAL_SECONDS = 10  # Interval between data fetches

def fetch_train_data(api_key, rt):
    """
    Fetches and extracts specified vehicle data from the CTA Train Tracker API.

    Args:
        api_key (str): Your CTA API key for authentication.
        rt (str): The train route to fetch data for.

    Returns:
        pd.DataFrame: A DataFrame containing the train data, including the route.
                      Returns an empty DataFrame if the request fails or no data is found.
    """
    params = {
        "key": api_key,
        "rt": rt,
        "outputType": "json"
    }
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

        ctatt_data = data.get('ctatt', {})
        timestamp = ctatt_data.get('tmst')
        route_data = ctatt_data.get('route', [])

        if not route_data:
            return pd.DataFrame()

        trains_list = route_data[0].get('train', [])
        if not trains_list:
            return pd.DataFrame()

        trains_df = pd.DataFrame(trains_list)
        trains_df['rt'] = route_data[0].get('@name')
        trains_df['tmst'] = timestamp # Use the top-level timestamp

        # Ensure all desired columns are present, fill missing ones with None
        for col in DATA_FIELDS:
            if col not in trains_df.columns:
                trains_df[col] = None
        
        return trains_df[DATA_FIELDS]

    except requests.exceptions.RequestException as e:
        print(f"Error making API request for route {rt}: {e}")
        return pd.DataFrame()
    except ValueError:
        print(f"Error decoding JSON from response for route {rt}: {response.text}")
        return pd.DataFrame()

def main():
    """
    Main function to run the data scraper. It collects data every 5 seconds
    between a specified start and end time and saves it to a CSV file.
    """
    if CTA_API_KEY == 'YOUR_CTA_API_KEY':
        print("Please replace 'YOUR_CTA_API_KEY' with your actual CTA API key.")
        return

    now = datetime.now()
    start_time_str = f"{now.year}-{now.month}-{now.day} {COLLECTION_START_TIME}"
    end_time_str = f"{now.year}-{now.month}-{now.day} {COLLECTION_END_TIME}"

    start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
    end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')

    # If the start time has already passed for today, schedule for tomorrow
    if datetime.now() > start_time:
        start_time += timedelta(days=1)
        end_time += timedelta(days=1)
        print(f"Start time is in the past. Scheduling for tomorrow at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    print(f"Waiting to start data collection at {start_time.strftime('%Y-%m-%d %H:%M:%S')}...")
    
    # Wait until the start time
    while datetime.now() < start_time:
        time.sleep(1)

    print(f"Starting data collection from {start_time.strftime('%H:%M:%S')} to {end_time.strftime('%H:%M:%S')}.")
    
    collected_data = []
    last_save_time = datetime.now()

    while datetime.now() < end_time:
        print(f"Fetching data at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        for rt in RT_PARAMS:
            train_data_df = fetch_train_data(CTA_API_KEY, rt)
            if not train_data_df.empty:
                collected_data.extend(train_data_df.to_dict('records'))
        
        # Wait for 5 seconds before the next fetch
        time.sleep(SAMPLE_INTERVAL_SECONDS)

        # Save data every hour
        if datetime.now() - last_save_time >= timedelta(hours=1):
            if collected_data:
                output_filename = f"cta_train_data_{last_save_time.strftime('%Y%m%d_%H%M%S')}.csv"
                df = pd.DataFrame(collected_data)
                df.to_csv(output_filename, index=False)
                print(f"Data for the past hour saved to {output_filename}")
                
                # Reset for the next hour
                collected_data = []
                last_save_time = datetime.now()

    # Final save for any remaining data
    if collected_data:
        output_filename = f"cta_train_data_{last_save_time.strftime('%Y%m%d_%H%M%S')}.csv"
        df = pd.DataFrame(collected_data)
        df.to_csv(output_filename, index=False)
        print(f"Final data batch saved to {output_filename}")

    print("Finished data collection.")

if __name__ == "__main__":
    main()


