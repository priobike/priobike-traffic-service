import json
import requests
import haversine
import time
import os


def main():

    #api = "https://iot.hamburg.de/v1.1/Datastreams?$filter=properties/serviceName eq 'HH_STA_HamburgerRadzaehlnetz' and properties/layerName eq 'Anzahl_Fahrraeder_Zaehlstelle_1-Stunde'&$expand=Observations($orderby=phenomenonTime desc;$top=1)"
    api = "https://iot.hamburg.de/v1.1/Datastreams?$filter=properties/serviceName eq 'HH_STA_AutomatisierteVerkehrsmengenerfassung' and properties/layerName eq 'Anzahl_Kfz_Zaehlstelle_15-Min'&$expand=Observations($orderby=phenomenonTime desc;$top=1)"

    data = {}

    counter = 0
    while api and counter < 5:
        # Fetch traffic data from API
        traffic_data = requests.get(api)
        if traffic_data.status_code != 200:
            raise Exception("Error fetching traffic data")
        traffic_data = traffic_data.json()

        # print json
        print(json.dumps(traffic_data, indent=4))

        for datapoint in traffic_data["value"]:
            try:
                id = datapoint["Observations"][0]["@iot.id"]
                coords = datapoint["observedArea"]["coordinates"]
                result = datapoint["Observations"][0]["result"]
                result_time = datapoint["Observations"][0]["resultTime"]
                print(id, coords, result, result_time)

                data.update({
                    "@iot.id": id,
                    "coordinates": coords,
                    "result": result,
                    "resultTime": result_time
                })
            except:
                continue
        counter += 1

        # get next API url, if available
        try:
            api = traffic_data["@iot.nextLink"]
            print(api)
        except:
            api = None


if __name__ == "__main__":
    main()
