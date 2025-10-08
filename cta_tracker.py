import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import requests

cta_api_key = 'edf3d5c3786946c490b5afceeedaf8da'

follow_url = 'https://lapi.transitchicago.com/api/1.0/ttfollow.aspx'
arrivals_url = 'http://lapi.transitchicago.com/api/1.0/ttarrivals.aspx'
positions_url = 'http://lapi.transitchicago.com/api/1.0/ttpositions.aspx'

# 1) get list of runnumbers by line
# 2) plot trains by line

def getRuns(rt):
    # rt is route color, e.g. "RED", "BLUE", "G", "P", "Y", "BR", "P"
    # returns list of run numbers for that line

    rns = []
    lats = []
    longs = []
    headings = []
    
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

    for train in trains_list:

        rns.append(train.get('rn'))
        lats.append(train.get('lat'))
        longs.append(train.get('lon'))
        headings.append(train.get('heading'))

    # print(rns)
    return(rns)

getRuns("RED")

def plotCity():
    # plot Chicago map
    geo_df = gpd.read_file ("cta_tracker/assets/neighborhoods/neighborhoods.shx")

    # Display the shapefile
    f, ax = plt.subplots(1, figsize=(8, 11))

    geo_df.plot(ax = ax, edgecolor='black')

    ax.set_title("Neighborhoods of Chicago", fontdict={'fontsize': '14', 'fontweight' : '3'})

    plt.title('Chicago Map')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')

    # return ax
    plt.show()

def main():
    plotCity()

