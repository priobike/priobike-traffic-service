import json
import os
import time

time_now = int(time.time())
time_60_days_ago = time_now - 60 * 60 * 24 * 60


def calculate_historic_average(hour_now, history_dir, files):
    """
    Build average for a given hour over max. last 60 days
    Returns the average score for the given hour or None if no data is available
    """

    global time_now, time_60_days_ago

    scores = []

    for filename in files:
        # Get timestamp from filename
        timestamp = time.mktime(time.strptime(filename, "%d.%m.%Y-%H:%M.json"))

        # Delete files older than 60 days. Files are sorted by date.
        if timestamp < time_60_days_ago:
            os.remove(f"{history_dir or 'history'}/{filename}")
            continue

        # extract hour from timestamp
        data_hour = int(time.strftime("%H", time.localtime(timestamp)))

        if data_hour == hour_now:
            # open json file and get score
            with open(f"{history_dir or 'history'}/{filename}", "r") as file:
                data = json.load(file)
                score = data["trafficflow"]
                scores.append(score)

    # Calculate average score
    if len(scores) != 0:
        return sum(scores) / len(scores)
    else:
        return None


def main(history_dir, prediction_path):
    """
    Read history json files and calculate average score for each hour to make a prediction
    """

    # Get files in the history folder
    files = os.listdir(history_dir or "history")
    files = [file for file in files if file.endswith(".json")]
    key = lambda x: int(time.mktime(time.strptime(x, "%d.%m.%Y-%H:%M.json")))
    files.sort(key=key, reverse=True)

    hour_now = int(time.strftime("%H", time.localtime()))

    prediction = {}

    # Get the average scores from hour -1 to hour +5
    for offset in range(-1, 5 + 1, 1):
        hour_score = calculate_historic_average(hour_now + offset, history_dir,
                                                files)
        prediction.update({hour_now + offset: hour_score})

    # Get the current score by reading the first file (which is the newest one, because the list is sorted)
    with open(f"{history_dir or 'history'}/{files[0]}", "r") as file:
        data = json.load(file)
        score_now = data["trafficflow"]
        prediction.update({"now": score_now})

    with open(prediction_path or "prediction.json", "w") as outfile:
        json.dump(prediction, outfile, indent=4)


if __name__ == "__main__":
    # Get an optional path under which the data should be saved
    import sys
    if len(sys.argv) > 1:
        history_dir = sys.argv[1]
        prediction_path = sys.argv[2]
    else:
        history_dir = None
        prediction_path = None

    main(history_dir, prediction_path)