import json
import requests
import haversine
import time
import os

# https://api.hamburg.de/datasets/v1/verkehrslage/api#/Data/features-verkehrslage

bulk = True # if true, all datapoints will be fetched (ignores limit), if false only the limit
limit = 50  # how many datapoints should be fetched (ignored if bulk is true)
api = "https://api.hamburg.de/datasets/v1/verkehrslage/collections/verkehrslage/items?limit=" + \
    str(limit) + "&offset=0&bulk=" + str(bulk) + "&f=json"

datapoints = 0

# calculates the distance between two points in meters
def calculate_distance(lat1, lon1, lat2, lon2):
    return haversine.haversine((lat1, lon1), (lat2, lon2), unit="m")

# calls the API and returns the raw JSON
def fetch_traffic_data():
    traffic_data = requests.get(api)

    if traffic_data.status_code == 200:
        return traffic_data.json()
    else:
        return None

# parses the raw JSON, calculates the length of each path and returns a dict with the id of a path and its length
def evaluate_JSON(trafficData):
    paths = {}
    global datapoints

    for datapoint in trafficData["features"]:
        id = datapoint["id"]
        coords = datapoint["geometry"]["coordinates"]
        datapoints += 1
        length_path = 0

        # interate over all coordinates except the last one
        for i in range(len(coords)-1):
            length_path += calculate_distance(coords[i][0],coords[i][1], coords[i+1][0], coords[i+1][1])

        traffic_status = datapoint["properties"]["zustandsklasse"]

        # calculate weight based on traffic status
        match traffic_status:
            case "gestaut":
                weight = 0
            case "zäh":
                weight = 0.33
            case "dicht":
                weight = 0.66
            case "fliessend":
                weight = 1
            case _:
                weight = 0

        paths.update({id: {"lengthPath": length_path, "trafficStatus": traffic_status, "weight": weight, "score": 0}})
    return paths


# converts the absolute length of each path to a relative value based on the total length of all paths between 0 and 1
def convert_absolute_pathlength_to_relative(paths):
    total_length = 0
    for path in paths:
        total_length += paths[path]["lengthPath"]

    for path in paths:
        paths[path]["lengthPath"] = paths[path]["lengthPath"]/total_length


# gives each path a score based on the relative length and the weight (traffic status)
def calculate_score(paths):
    for path in paths:
        paths[path]["score"] = paths[path]["lengthPath"] * paths[path]["weight"]

# writes the data to a json file
def write_file(paths):
    sum_score = 0
    for path in paths:
        sum_score += paths[path]["score"]

    date = time.strftime("%d.%m.%Y", time.localtime())
    hour = time.strftime("%H:%M", time.localtime())

    timestamp = time.time()

    # save data to json file
    with open("history/" + str(date) + " " + str(hour) + ".json", "w") as outfile:
        write = {"score": sum_score, "timestamp": timestamp, "datapoints": datapoints}
        json.dump(write, outfile, indent=4)


def main():
    # create folder for data if it doesn't exist
    if not os.path.exists("history"):
        os.makedirs("history")

    # fetch traffic data from API
    trafficData = fetch_traffic_data()

    # if no data was fetched, exit
    if trafficData == None:
        return

    paths = evaluate_JSON(trafficData)

    convert_absolute_pathlength_to_relative(paths)

    calculate_score(paths)

    write_file(paths)

if __name__ == "__main__":
    main()
