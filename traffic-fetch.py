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
def calculateDistance(lat1, lon1, lat2, lon2):
    return haversine.haversine((lat1, lon1), (lat2, lon2), unit="m")

# calls the API and returns the raw JSON
def fetchTrafficData():
    trafficData = requests.get(api)

    if trafficData.status_code == 200:
        return trafficData.json()
    else:
        return None

# parses the raw JSON, calculates the length of each path and returns a dict with the id of a path and its length
def evaulateJSON(trafficData):
    paths = {}
    global datapoints

    for datapoint in trafficData["features"]:
        id = datapoint["id"]
        coords = datapoint["geometry"]["coordinates"]
        datapoints += 1
        lengthPath = 0

        # interate over all coordinates except the last one
        for i in range(len(coords)-1):
            lengthPath += calculateDistance(coords[i][0],coords[i][1], coords[i+1][0], coords[i+1][1])

        trafficStatus = datapoint["properties"]["zustandsklasse"]

        # calculate weight based on traffic status
        match trafficStatus:
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

        paths.update({id: {"lengthPath": lengthPath, "trafficStatus": trafficStatus, "weight": weight, "score": 0}})
    return paths


# converts the absolute length of each path to a relative value based on the total length of all paths between 0 and 1
def convertAbsolutePathLengthToRelative(paths):
    totalLength = 0
    for path in paths:
        totalLength += paths[path]["lengthPath"]

    for path in paths:
        paths[path]["lengthPath"] = paths[path]["lengthPath"]/totalLength


# gives each path a score based on the relative length and the weight (traffic status)
def calculateScore(paths):
    for path in paths:
        paths[path]["score"] = paths[path]["lengthPath"] * paths[path]["weight"]

# writes the data to a json file
def writeFile(paths):
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
    trafficData = fetchTrafficData()

    # if no data was fetched, exit
    if trafficData == None:
        return

    paths = evaulateJSON(trafficData)

    convertAbsolutePathLengthToRelative(paths)

    calculateScore(paths)

    writeFile(paths)

if __name__ == "__main__":
    main()
