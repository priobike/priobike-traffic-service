import os
import time
import json

time_now = int(time.time())
time_7_days_ago = time_now - 60 * 60 * 24 * 7


def calculate_historic_average(hour_now, files):
    """
    Build average for a given hour over max. last 7 days
    Returns the average score for the given hour or None if no data is available
    """

    global time_now, time_7_days_ago

    scores = []

    for filename in files:
        # get timestamp from filename
        timestamp = time.mktime(time.strptime(filename, "%d.%m.%Y-%H:%M.json"))

        # discard files older than 7 days. Files are sorted by date, therefore break at first file older than 7 days
        if timestamp < time_7_days_ago:
            break

        # extract hour from timestamp
        data_hour = int(time.strftime("%H", time.localtime(timestamp)))

        if data_hour == hour_now:
            # open json file and get score
            with open(f"history/{filename}", "r") as file:
                data = json.load(file)
                score = data["trafficflow"]
                scores.append(score)

    # Calculate average score
    if len(scores) != 0:
        return sum(scores) / len(scores)
    else:
        return None


def main():
    """
    Read history json files and calculate average score for each hour to make a prediction
    """

    # Get files in the history folder
    files = os.listdir("history")
    files = [file for file in files if file.endswith(".json")]
    files.sort(reverse=True)

    hour_now = int(time.strftime("%H", time.localtime()))

    prediction = {}

    # Get the average scores from hour -1 to hour +5
    for offset in range(-1, 5 + 1, 1):
        hour_score = calculate_historic_average(hour_now + offset, files)
        prediction.update({hour_now + offset: hour_score})

        print("Hour:", hour_now + offset, "\tScore:", hour_score)

    with open(f"prediction.json", "w") as outfile:
        json.dump(prediction, outfile, indent=4)


if __name__ == "__main__":
    main()