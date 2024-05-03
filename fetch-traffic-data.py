import json
import os
import time

import haversine
import requests
import random

def main():
    """
    Fetch the traffic data and write it to a history json file.
    """

    worker = os.environ["WORKER"]
    if worker is None:
        raise ValueError('Worker is not specified')
    
    history_dir = os.environ.get("HISTORY_DIR") 
    if history_dir is None:
        raise ValueError('History directory is not specified')

    # Check if the script is running as a worker or manager
    if worker == "true":
        worker_fetch(history_dir)
    else:
        manager_fetch(history_dir)

def manager_fetch(history_dir):
    """
    Fetch the traffic data from the api and write it to a history json file.
    """

    api_link = f"https://api.hamburg.de/datasets/v1/verkehrslage/collections/verkehrslage/items?&f=json&limit=100&offset=0"

    # Create folder for data if it doesn't exist
    if not os.path.exists(history_dir or 'history'):
        os.makedirs(history_dir or 'history')

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
    with open(f"{history_dir or 'history'}/{date}-{hour}.json", "w") as outfile:
        write = {"trafficflow": sum_score, "timestamp": timestamp, "paths": len(paths)}
        json.dump(write, outfile, indent=4)

    # List all files in the history directory
    files = os.listdir(history_dir or 'history')
    files = [file for file in files if file.endswith(".json")]

    # Save all file names to a file in history_dir
    with open(os.path.join(history_dir, "history_files.txt"), "w") as f:
        for file in files:
            f.write(file + "\n")

def worker_fetch(history_dir):
    """
    Fetch the traffic data from the manager and write it to a history json file.
    """
    
    host = os.environ.get("HOST")
    if host is None:
        raise ValueError('Host is not specified')
    
    # wait for a random amount of time and retry
    time.sleep(random.randint(10, 30))

    history_files_link = f"http://{host}/history/history_files.txt"

    # Create folder for data if it doesn't exist
    if not os.path.exists(history_dir or 'history'):
        os.makedirs(history_dir or 'history')

    # Fetch history files from manager
    response = requests.get(history_files_link)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch history files from {history_files_link}")
    
    if response.text == "":
        raise ValueError('No history files found on manager')
    
    # Fetch files in history folder
    old_files = os.listdir(history_dir or "history")
    old_files = [file for file in old_files if file.endswith(".json")]

    # Parse the response
    files = response.text.split("\n")
    files = [file for file in files if file.endswith(".json")]

    # Get the diff of both file lists.
    new_files = list(set(files) - set(old_files))
    
    if len(new_files) == 0:
        worker_fetch(history_dir)
        return

    for file in new_files:
        file_link = f"http://{host}/history/{file}"
        print(f"Downloading {file} from {file_link}")

        response = requests.get(file_link)
        response.raise_for_status()
        data = response.json()

        # Save data to file
        with open(f"{history_dir or 'history'}/{file}", "w") as outfile:
            json.dump(data, outfile, indent=4)

if __name__ == "__main__":
    # Get an optional path under which the data should be saved

    main()
