import json
import os
import time

from push import push_to_workers

days_to_include = 900  # How many days to include in the prediction, older data will be automatically deleted
time_now = int(time.time())
time_oldest = time_now - 60 * 60 * 24 * days_to_include
date_now = time.strftime("%d.%m.%Y", time.localtime())
weekday_now = int(time.strftime("%w", time.localtime()))


def main(prediction_path):
    """
    Read history json files and calculate average score for each hour to make a prediction
    Build average for a given hour over max. last 60 days (see "days_to_include")
    There are 3 different quality levels for the prediction:
    It first tries to get the score for the given hour and same day of the week (marked in prediction.json as high quality)
    If there is not enough data, it tries to get the score for the given hour within the whole workweek/weekend (marked in prediction.json as medium quality)
    If there is still not enough data, it tries to get the score for the given hour, no matter the day (marked in prediction.json as low quality)
    """
    
    global date_now, weekday_now

    # Get files in the history folder
    files = os.listdir("/app/history")
    files = [file for file in files if file.endswith(".json")]
    key = lambda x: int(time.mktime(time.strptime(x, "%d.%m.%Y-%H:%M.json")))
    files.sort(key=key, reverse=True)

    prune_old_files(files)

    hour_now = int(time.strftime("%H", time.localtime()))
    prediction = {}

    # Get the average scores from hour now-1 to hour now+5
    for offset in range(-1, 5 + 1, 1):
        # Check if we need to look at the next day
        hour_to_check = (hour_now + offset) % 24
        if hour_to_check != (hour_now + offset):
            # Switch to next day
            t = time_now + (60 * 60 * 24)
            date_now = time.strftime("%d.%m.%Y", time.localtime(t))
            weekday_now = int(time.strftime("%w", time.localtime(t)))
            
        prediction_data = use_same_day(hour_to_check, files)
        if prediction_data is not None:
            prediction.update({hour_to_check: prediction_data})
            prediction.update({"quality_" + str(hour_to_check): "high"})
            continue
        
        prediction_data = use_weekday_or_weekend(hour_to_check, files)
        if prediction_data is not None:
            prediction.update({hour_to_check: prediction_data})
            prediction.update({"quality_" + str(hour_to_check): "medium"})
            continue
        
        prediction_data = use_same_hour(hour_to_check, files)
        if prediction_data is not None:
            prediction.update({hour_to_check: prediction_data})
            prediction.update({"quality_" + str(hour_to_check): "low"})
            continue
        
        prediction.update({hour_to_check: None})
        prediction.update({"quality_" + str(hour_to_check): None})

    # Get the current score by reading the first file (which is the newest one, because the list is sorted)
    with open(f"/app/history/{files[0]}", "r") as file:
        data = json.load(file)
        score_now = data["trafficflow"]
        prediction.update({"now": score_now})

    with open(prediction_path or "prediction.json", "w") as outfile:
        json.dump(prediction, outfile, indent=4)
        push_to_workers("prediction.json", json.dumps(prediction))


def prune_old_files(files):
    """
    Deletes files older than 60 days (see "days_to_include").
    """

    global time_oldest

    removed = []
    for filename in files:
        # Get timestamp from filename
        timestamp = time.mktime(time.strptime(filename, "%d.%m.%Y-%H:%M.json"))

        # Delete files old files
        if timestamp < time_oldest:
            os.remove(f"/app/history/{filename}")
            removed.append(filename)

    for filename in removed:
        files.remove(filename)


def use_same_day(check_hour, files):
    """
    Get the score for the given hour and same day of the week (marked in prediction.json as high quality)
    """
    global date_now, weekday_now
    scores = []
    for filename in files:
        # Get timestamp from filename
        timestamp = time.mktime(time.strptime(filename, "%d.%m.%Y-%H:%M.json"))

        # extract time from timestamp
        data_day = int(time.strftime("%w", time.localtime(timestamp)))
        data_hour = int(time.strftime("%H", time.localtime(timestamp)))
        data_date = time.strftime("%d.%m.%Y", time.localtime(timestamp))

        # If we have data for the given hour and same day of the week
        if data_hour == check_hour and data_day == weekday_now and data_date != date_now:
            with open(f"/app/history/{filename}", "r") as file:
                data = json.load(file)
                score = data["trafficflow"]
                scores.append(score)

    # Return average score
    return sum(scores) / len(scores) if len(scores) != 0 else None


def use_weekday_or_weekend(check_hour, files):
    """
    Get the score for the given hour within the whole workweek/weekend (marked in prediction.json as medium quality)
    """

    global date_now, weekday_now
    scores = []
    for filename in files:
        # Get timestamp from filename
        timestamp = time.mktime(time.strptime(filename, "%d.%m.%Y-%H:%M.json"))

        # extract time from timestamp
        data_day = int(time.strftime("%w", time.localtime(timestamp)))
        data_hour = int(time.strftime("%H", time.localtime(timestamp)))

        # If there is not enough data, get the average score for the given hour on workweek/weekend
        if weekday_now <= 5:
            # workweek
            if data_hour == check_hour and data_day <= 5:
                with open(f"/app/history/{filename}",
                          "r") as file:
                    data = json.load(file)
                    score = data["trafficflow"]
                    scores.append(score)
                continue
        else:
            # weekend
            if data_hour == check_hour and data_day > 5:
                with open(f"/app/history/{filename}",
                          "r") as file:
                    data = json.load(file)
                    score = data["trafficflow"]
                    scores.append(score)

    # Return average score
    return sum(scores) / len(scores) if len(scores) != 0 else None


def use_same_hour(check_hour, files):
    """
    Get the score for the given hour, no matter the day or weekend/weekday (marked in prediction.json as low quality)
    """

    scores = []
    for filename in files:
        # Get timestamp from filename
        timestamp = time.mktime(time.strptime(filename, "%d.%m.%Y-%H:%M.json"))

        # extract time from timestamp
        data_hour = int(time.strftime("%H", time.localtime(timestamp)))

        # If there is not enough data, get the average score for the given hour
        if data_hour == check_hour:
            with open(f"/app/history/{filename}", "r") as file:
                data = json.load(file)
                score = data["trafficflow"]
                scores.append(score)

    # Return average score
    return sum(scores) / len(scores) if len(scores) != 0 else None


if __name__ == "__main__":
    import sys

    # Get an optional path under which the data should be saved
    if len(sys.argv) > 1:
        prediction_path = sys.argv[1]
    else:
        prediction_path = None

    main(prediction_path)