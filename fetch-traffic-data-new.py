import json
import requests
import haversine
import time
import os


def main():

    #api = "https://iot.hamburg.de/v1.1/Datastreams?$filter=properties/serviceName eq 'HH_STA_HamburgerRadzaehlnetz' and properties/layerName eq 'Anzahl_Fahrraeder_Zaehlstelle_1-Stunde'&$expand=Observations($orderby=phenomenonTime desc;$top=1)"
    api = "https://iot.hamburg.de/v1.1/Datastreams?$filter=properties/serviceName eq 'HH_STA_AutomatisierteVerkehrsmengenerfassung' and properties/layerName eq 'Anzahl_Kfz_Zaehlstelle_15-Min'&$expand=Observations($orderby=phenomenonTime desc;$top=1)"

    data = {}
    total_result = 0

    while api:
        # Fetch traffic data from API
        traffic_data = requests.get(api)
        if traffic_data.status_code != 200:
            raise Exception("Error fetching traffic data")
        traffic_data = traffic_data.json()

        for datapoint in traffic_data["value"]:
            try:
                id = datapoint["Observations"][0]["@iot.id"]
                coords = datapoint["observedArea"]["coordinates"]
                cars = int(datapoint["Observations"][0]["result"])
                timestamp = datapoint["Observations"][0]["resultTime"]

                # Skip data with 0 cars
                if cars == 0:
                    continue

                # Skip data older than 2 hours
                time_check = time.mktime(
                    time.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ"))
                if 7200 < (time.time() - time_check):
                    continue

                data.update({
                    id: {
                        "coordinates": coords,
                        "totalCars": cars,
                        "share": 0,
                        "timestamp": timestamp
                    }
                })

                total_result += cars

            except:
                continue

        # Calculate share of cars
        for datapoint in data:
            data[datapoint][
                "share"] = data[datapoint]["totalCars"] / total_result

        # get next API url, if available
        try:
            api = traffic_data["@iot.nextLink"]
        except:
            api = None

    # Create folder for data if it doesn't exist
    if not os.path.exists("history"):
        os.makedirs("history")

    date = time.strftime("%d.%m.%Y", time.localtime())
    hour = time.strftime("%H:%M", time.localtime())

    timestamp = int(time.time())

    # save data to JSON history file
    with open(f"history/{date}-{hour}.json", "w") as outfile:
        write = {
            "cars": total_result,
            "timestamp": timestamp,
            "data": data,
        }
        json.dump(write, outfile, indent=4)


if __name__ == "__main__":
    main()
