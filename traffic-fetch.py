import json
import requests
import haversine

# https://api.hamburg.de/datasets/v1/verkehrslage/api#/Data/features-verkehrslage

bulk = True # if true, all datapoints will be fetched (ignores limit), if false only the limit
limit = 50  # how many datapoints should be fetched (ignored if bulk is true)
api = "https://api.hamburg.de/datasets/v1/verkehrslage/collections/verkehrslage/items?limit=" + \
    str(limit) + "&offset=0&bulk=" + str(bulk) + "&f=json"


# calculates the distance between two points in meters
def calculateDistance(lat1, lon1, lat2, lon2):
    return haversine.haversine((lat1, lon1), (lat2, lon2), unit="m")

# calls the API and returns the raw JSON
def getTrafficData():
    trafficData = requests.get(api)

    if trafficData.status_code == 200:
        print("Successly fetched traffic data")
        return trafficData.json()
    else:
        print("Error fetching traffic data from API, status code: " +
              str(trafficData.status_code))
        return None

# parses the raw JSON, calculates the length of each path and returns a dict with the id of a path and its length
def evaulateJSON(trafficData):

    # print(json.dumps(trafficData, indent=4))

    paths = {}
    datapoints = 0

    for datapoint in trafficData["features"]:
        id = datapoint["id"]
        coords = datapoint["geometry"]["coordinates"]
        datapoints += 1
        lengthPath = 0

        # interate over all coordinates except the last one
        for i in range(len(coords)-1):
            lengthPath += calculateDistance(coords[i][0],
                                            coords[i][1], coords[i+1][0], coords[i+1][1])

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

        paths.update(
            {id: {"lengthPath": lengthPath, "trafficStatus": trafficStatus, "weight": weight, "score": 0}})
    print("Number Datapoints: " + str(datapoints))
    return paths


# converts the absolute length of each path to a relative value based on the total length of all paths between 0 and 1
def convertAbsolutePathlengthToRelative(paths):
    totalLength = 0
    for path in paths:
        totalLength += paths[path]["lengthPath"]
    print("Total length of all paths: " + str(totalLength) +
          "m " + str(round(totalLength/1000, 2)) + "km")

    for path in paths:
        paths[path]["lengthPath"] = paths[path]["lengthPath"]/totalLength


# gives each path a score based on the relative length and the weight (traffic status)
def calculateScore(paths):
    for path in paths:
        paths[path]["score"] = paths[path]["lengthPath"] * paths[path]["weight"]


def main():
    # fetch traffic data from API
    trafficData = getTrafficData()

    # if no data was fetched, exit
    if trafficData == None:
        return

    # parse JSON and calculate absolute length of each path
    paths = evaulateJSON(trafficData)

    # convert absolute length of each path to a relative value
    convertAbsolutePathlengthToRelative(paths)

    # calculate score for each path by multiplying the relative length with the weight
    calculateScore(paths)

    sum_score = 0
    for path in paths:
        # print("Path:" + str(path) + ", length: " + str(round(paths[path]["lengthPath"]*100, 4)) + " %, traffic: " + paths[path]["trafficStatus"] + ", score: " + str(round(paths[path]["score"], 4)))
        sum_score += paths[path]["score"]
    print("Sum of all scores: " + str(sum_score))


if __name__ == "__main__":
    main()
