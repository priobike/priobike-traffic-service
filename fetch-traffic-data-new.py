import json
import requests
import haversine
import time
import os

api = "https://iot.hamburg.de/v1.1/Datastreams?$filter=properties/serviceName eq 'HH_STA_HamburgerRadzaehlnetz' and properties/layerName eq 'Anzahl_Fahrraeder_Zaehlstelle_1-Stunde'&$expand=Observations($orderby=phenomenonTime desc;$top=1)"


def main():

    # print as json
    # print(json.dumps(traffic_data, indent=4))

    data = {}
    next_url = True

    counter = 0
    while next_url and counter < 5:
        # Fetch traffic data from API
        traffic_data = requests.get(api)
        if traffic_data.status_code != 200:
            raise Exception("Error fetching traffic data")
        traffic_data = traffic_data.json()

        for datapoint in traffic_data["value"]:
            id = datapoint["Observations"][0]["@iot.id"]
            coords = datapoint["observedArea"]["coordinates"]
            result = datapoint["Observations"][0]["result"]
            result_time = datapoint["Observations"][0]["resultTime"]
            print(id, coords, result, result_time)
            # print(datapoint["Observations"][0]["result"])

            data.update({
                "id": id,
                "coords": coords,
                "result": result,
                "result_time": result_time
            })
        counter += 1

        # get next API url, if available
        try:
            next_url = traffic_data["@iot.nextLink"]
            print(next_url)
        except:
            next_url = None


if __name__ == "__main__":
    main()
