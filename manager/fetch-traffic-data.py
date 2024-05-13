import json
import os
import time

import haversine
import requests

def main():
    """
    Fetch the traffic data and write it to a history json file.
    """

    api_link = f"https://api.hamburg.de/datasets/v1/verkehrslage/collections/verkehrslage/items?&f=json&limit=100&offset=0"

    # Create folder for data if it doesn't exist
    if not os.path.exists('history'):
        os.makedirs('history')

    # Fetch traffic data from API
    traffic_data = []
    page = 0
    while True:
        print(f'Downloading page {page} from {api_link}')
        response = requests.get(api_link)
        response.raise_for_status()
        response_json = response.json()
        if 'features' and 'links' not in response_json:
            raise Exception('Missing value in response')
        for feature in response_json['features']:
            traffic_data.append(feature)
        for link in response_json["links"]:
            if link["rel"] == "next":
                next_link = link["href"]
        if api_link == next_link:
            print('Finished downloading all traffic data')
            break
        api_link = next_link
        page += 1

    # Parse the api data
    paths = {}
    for datapoint in traffic_data:
        id = datapoint["id"]

        # Sum up the length along the linestring.
        length = 0
        coords = datapoint["geometry"]["coordinates"]
        for i in range(len(coords)-1):
            lat1, lon1 = coords[i][0], coords[i][1]
            lat2, lon2 = coords[i+1][0], coords[i+1][1]
            length += haversine.haversine((lat1, lon1), (lat2, lon2), unit="m")

        # Calculate weight based on traffic status
        c = datapoint["properties"]["zustandsklasse"]
        if c == "gestaut":
            weight = 0
        elif c == "zäh":
            weight = 1/3
        elif c == "dicht":
            weight = 2/3
        elif c == "fliessend":
            weight = 1
        else:
            weight = 0

        paths.update({id: {
            "length": length, 
            "weight": weight,
        }})

    # Calculate the score for each path, relative to the total length of all paths
    total_length = sum([paths[path]["length"] for path in paths])
    for path in paths:
        paths[path]["score"] = (paths[path]["length"]/total_length) * paths[path]["weight"]
    
    # Write the data to a json file
    sum_score = sum([paths[path]["score"] for path in paths])

    date = time.strftime("%d.%m.%Y", time.localtime())
    hour = time.strftime("%H:%M", time.localtime())

    timestamp = int(time.time())

    # save data to json file
    with open(f"history/{date}-{hour}.json", "w") as outfile:
        write = {"trafficflow": sum_score, "timestamp": timestamp, "paths": len(paths)}
        json.dump(write, outfile, indent=4)

if __name__ == "__main__":
    main()