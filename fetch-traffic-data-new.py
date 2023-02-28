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
                result = datapoint["Observations"][0]["result"]
                result_time = datapoint["Observations"][0]["resultTime"]

                # Skip data not from today
                today = time.strftime("%Y-%m-%d", time.localtime())
                if not result_time.startswith(today):
                    continue

                data.update({
                    id: {
                        "coordinates": coords,
                        "totalCars": result,
                        "share": 0,
                        "time": result_time
                    }
                })

                total_result += result

                # # check if coords contain a list of coordinates
                # if isinstance(coords[0], list):
                #     print("List of coordinates")

            except:
                continue

        print("Total cars seen:", total_result)

        # Calculate share of cars
        for datapoint in data:
            data[datapoint][
                "share"] = data[datapoint]["totalCars"] / total_result

        # get next API url, if available
        try:
            api = traffic_data["@iot.nextLink"]
            # print(api)
        except:
            print("No more data available")
            api = None

    # Create folder for data if it doesn't exist
    if not os.path.exists("history"):
        os.makedirs("history")

    date = time.strftime("%d.%m.%Y", time.localtime())
    hour = time.strftime("%H:%M", time.localtime())

    timestamp = int(time.time())

    # save data to json file
    with open(f"history/{date}-{hour}.json", "w") as outfile:
        write = {
            "cars": total_result,
            "timestamp": timestamp,
            "data": data,
        }
        json.dump(write, outfile, indent=4)

    print("Done")


if __name__ == "__main__":
    main()
