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
DATA_FIELDS = ['tmst', 'rn', 'lat', 'lon', 'hdg']

def fetch_train_data(api_key):
    """
    Fetches and extracts specified vehicle data from the CTA Bus Tracker API.

    Args:
        api_key (str): Your CTA API key for authentication.

    Returns:
        list: A list of dictionaries, where each dictionary contains the
              data for a single vehicle. Returns an empty list if the request fails.
    """
    all_train_data = []
    params = {
        "key": CTA_API_KEY,
        "rt": "RED",
        "outputType": "JSON"
    }
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()  # Or response.text for non-JSON responses

        # Process the data
        # Extract the list of trains
        trains_list = data.get('ctatt', {}).get('route', [{}])[0].get('train', [])

        # Create a pandas DataFrame from the list of trains
        trains_df = pd.DataFrame(trains_list)

        # Extract only the desired columns
        trains_info_df = trains_df[['prdt', 'rn', 'lat', 'lon', 'heading']]

        # Display the DataFrame with selected columns
        # display(trains_info_df)
        return trains_info_df
    
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")

def main():
    """
    Main function to run the data scraper. It collects data every 5 seconds
    for 5 minutes and saves it to a CSV file.
    """
    if CTA_API_KEY == 'YOUR_CTA_API_KEY':
        print("Please replace 'YOUR_CTA_API_KEY' with your actual CTA API key.")
        return

    print("Starting 5-minute data collection...")
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=5)
    
    collected_data = []

    while datetime.now() < end_time:
        print(f"Fetching data at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        train_data = fetch_train_data(CTA_API_KEY)
        if not train_data.empty:
            collected_data.extend(train_data.to_dict('records'))
        
        # Wait for 5 seconds before the next fetch
        time.sleep(2)

    print("Finished data collection.")

    # Convert the list of dictionaries to a pandas DataFrame
    if collected_data:
        df = pd.DataFrame(collected_data)
        # Save the DataFrame to a CSV file
        output_filename = 'cta_train_data.csv'
        df.to_csv(output_filename, index=False)
        print(f"Data successfully saved to {output_filename}")
    else:
        print("No data was collected. DataFrame was not created.")

if __name__ == "__main__":
    main()


