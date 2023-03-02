import json
import os
import time

import haversine
import requests

api = f"https://api.hamburg.de/datasets/v1/verkehrslage/collections/verkehrslage/items?&offset=0&bulk=True&f=json"

def main(history_dir):
    """
    Fetch the traffic data and write it to a history json file.
    """

    # Create folder for data if it doesn't exist
    if not os.path.exists(history_dir or 'history'):
        os.makedirs(history_dir or 'history')

    # Fetch traffic data from API
    traffic_data = requests.get(api)
    if traffic_data.status_code != 200:
        raise Exception("Error fetching traffic data")
    traffic_data = traffic_data.json()

    # Parse the api data
    paths = {}
    for datapoint in traffic_data["features"]:
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
    with open(f"{history_dir or 'history'}/{date}-{hour}.json", "w") as outfile:
        write = {"trafficflow": sum_score, "timestamp": timestamp, "paths": len(paths)}
        json.dump(write, outfile, indent=4)

if __name__ == "__main__":
    # Get an optional path under which the data should be saved
    import sys
    if len(sys.argv) > 1:
        history_dir = sys.argv[1]
    else:
        history_dir = None

    main(history_dir)
