import json
import requests
import time
import os

total_cars = 0
total_bikes = 0
data_cars = {}
data_bikes = {}


def fetch_api(api_type):
    """
    Fetch, filter and evaluate API data for the amount of cars or bikes recently counted in Hamburg.
    """

    if api_type == "cars":
        api = "https://iot.hamburg.de/v1.1/Datastreams?$filter=properties/serviceName eq 'HH_STA_AutomatisierteVerkehrsmengenerfassung' and properties/layerName eq 'Anzahl_Kfz_Zaehlstelle_15-Min'&$expand=Observations($orderby=phenomenonTime desc;$top=1)"
    elif api_type == "bikes":
        api = "https://iot.hamburg.de/v1.1/Datastreams?$filter=properties/serviceName%20eq%20%27HH_STA_HamburgerRadzaehlnetz%27%20and%20properties/layerName%20eq%20%27Anzahl_Fahrraeder_Zaehlstelle_15-Min%27&$expand=Observations($orderby=phenomenonTime%20desc;$top=1)"
    else:
        raise Exception("Invalid API type")

    global total_cars
    global total_bikes
    global data_cars
    global data_bikes

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
                amount = int(datapoint["Observations"][0]["result"])
                timestamp = datapoint["Observations"][0]["resultTime"]

                # Skip data with 0 cars/bikes
                if amount == 0:
                    continue

                # Skip data older than 2 hours
                time_check = time.mktime(
                    time.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ"))
                if 7200 < (time.time() - time_check):
                    continue

                if api_type == "cars":
                    data_cars.update({
                        id: {
                            "coordinates": coords,
                            "totalCars": amount,
                            "share": 0,
                            "timestamp": timestamp
                        }
                    })
                    total_cars += amount
                if api_type == "bikes":
                    data_bikes.update({
                        id: {
                            "coordinates": coords,
                            "totalBikes": amount,
                            "share": 0,
                            "timestamp": timestamp
                        }
                    })
                    total_bikes += amount

            except:
                continue

        # Calculate share of cars/bikes
        if api_type == "cars":
            for datapoint in data_cars:
                data_cars[datapoint][
                    "share"] = data_cars[datapoint]["totalCars"] / total_cars
        if api_type == "bikes":
            for datapoint in data_bikes:
                data_bikes[datapoint]["share"] = data_bikes[datapoint][
                    "totalBikes"] / total_bikes

        # get next API url, if available
        try:
            api = traffic_data["@iot.nextLink"]
        except:
            api = None


def main():
    """
    Write data to JSON history file after fetching it from the API.
    """

    fetch_api("cars")
    fetch_api("bikes")

    # Create folder for data if it doesn't exist
    if not os.path.exists("history"):
        os.makedirs("history")

    date = time.strftime("%d.%m.%Y", time.localtime())
    hour = time.strftime("%H:%M", time.localtime())

    timestamp = int(time.time())

    # Save data to JSON history file
    with open(f"history/{date}-{hour}.json", "w") as outfile:
        write = {
            "cars": total_cars,
            "bikes": total_bikes,
            "timestamp": timestamp,
            "dataCars": data_cars,
            "dataBikes": data_bikes,
        }
        json.dump(write, outfile, indent=4)


if __name__ == "__main__":
    main()
